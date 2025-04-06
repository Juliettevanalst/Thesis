# Import important libraries
import geopandas as gpd
import numpy as np
import os
from shapely.geometry import Point, Polygon
from scipy.spatial import Voronoi
import matplotlib.pyplot as plt
from shapely.ops import unary_union
import random
from scipy.spatial import cKDTree
import networkx as nx
from mesa import Model, Agent
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector

from Agents2 import Agri_small_saline, Agri_small_fresh


class RiverDeltaModel(Model):
    def __init__(self, seed=20, province = 'Bac Lieu',
    num_agents = {"Agri_small_saline": 200, "Agri_small_fresh": 200},
    salinity_shock_step = [120, 600]): #, "Agri_middle_saline":0, "Agri_middle_fresh": 0, "Agri_corporate_saline":0, "Agri_corporate_fresh": 0, "Aqua_small":20}):

        super().__init__(seed = seed)

        self.seed = seed
        random.seed(20)
        np.random.seed(20)

        # Create area
        self.province = province 
        self.polygon = self.gather_shapefiles(province) 
        self.G = self.initialize_network(self.polygon, sum(num_agents.values()), seed=self.seed)
        self.grid = NetworkGrid(self.G)

        # Possibility for a shock
        self.salinity_shock_step = salinity_shock_step
        self.salinity_shock = False

        # Set up data collector
        model_metrics = {}
        agent_metrics = {"Age":'ages', "Salinity": 'salinity', "Savings":"savings", "Loan_size": 'loan_size','maximum_debt':"maximum_debt", 'income':'income', 'abilities':'abilities', 'current_crop':'current_crop', "New crop":"new_crop"}
        self.datacollector = DataCollector(model_reporters = model_metrics, agent_reporters = agent_metrics)

        # Create agents
        self.num_agents = num_agents
        available_nodes = list(self.G.nodes())
        random.shuffle(available_nodes)

        agent_classes = { "Agri_small_saline": Agri_small_saline, "Agri_small_fresh": Agri_small_fresh}
        # , "Agri_middle_saline": Agri_middle_saline,
        # "Agri_middle_fresh": Agri_middle_fresh,"Agri_corporate_saline": Agri_corporate_saline, "Agri_corporate_fresh": Agri_corporate_fresh,
        # "Aqua_small": Aqua_small}

        for agent_type, count in num_agents.items():
            AgentClass = agent_classes[agent_type]
            for i in range(count):
                node_id = available_nodes.pop(0)
                agent = AgentClass(self, agent_type, node_id)
                self.agents.add(agent)
                self.grid.place_agent(agent, node_id)
        
    
    def step(self):
        self.agents.shuffle_do('step')

        if self.steps % 12 == 0:
            # Check if a shock is happening
            if self.steps in self.salinity_shock_step:
                self.salinity_shock = True
                for agent in self.agents:
                    agent.salinity = random.uniform (1.5, 2) * agent.salinity # NEED TO DECIDE TOMORROW WITH SEPHER HOW TO DO THIS
            
            if self.steps in [step + 12 for step in self.salinity_shock_step]: # I make the assumption that a shock is happening the whole year
                self.salinity_shock = False
                for agent in self.agents:
                    agent.salinity = 1.05 * agent.salinity # NEED TO DECIDE TOMORROW WITH SEPTHER HOW TO DO THIS

            self.agents.do("yearly_activities")

            # Collect data
            self.datacollector.collect(self)

            # Set income to zero, to calculate everything new for the next year
            self.agents.do("reset_income")
                
        
        yieldtime_crops = {"Rice":6, "Mango":12, "Coconut": 12}
        self.agents.do(lambda agent: agent.harvest() if self.steps % yieldtime_crops[agent.current_crop]==0 else None)


    def gather_shapefiles(self, province):
        # Define path
        path = os.getcwd()

        # Import dataset
        path = path + "\\provinces_area.shp"
        gdf = gpd.read_file(path)

        # Select correct province, and set it in meters using epsg
        gdf_correct_province = gdf[gdf['Name']==province]
        gdf_correct_province = gdf_correct_province.to_crs(epsg=28992) 

        # Create polygon
        polygon = gdf_correct_province.unary_union
        s = gpd.GeoSeries(polygon)
        return s

    def initialize_network(self, polygon, num_agents, seed):
        
        # Define number of points
        points = polygon.sample_points(size=num_agents, seed = seed)

        points_list = list(points.geometry[0].geoms)
        coords = np.array([(pt.x, pt.y) for pt in points_list])

        # Create a network, three nearest nodes are supposed to be your neighbours
        tree = cKDTree(coords)
        k = 4  
        distances, indices = tree.query(coords, k=k)

        G = nx.Graph()

        # Add nodes
        for i, (x, y) in enumerate(coords):
            G.add_node(i, pos=(x, y))

        # Add edges
        for i, neighbors in enumerate(indices):
            for j in neighbors[1:]:  # skip the first one, that is the point itself
                G.add_edge(i, j)

        return G
