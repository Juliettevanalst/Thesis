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

from Agents2 import Agri_farmer, Agri_small_saline, Agri_small_fresh, Low_skilled_wage_worker, Migrated, Aqua_small_saline, Aqua_farmer, Service_workers


class RiverDeltaModel(Model):
    def __init__(self, seed=20, district = 'Nhà Bè',
    num_agents = {"Agri_small_saline": 50, "Agri_small_fresh": 50, "Aqua_small_saline":50},
    num_low_skilled_ww = {"Aqua":10, "Agri": 10},
    num_service_workers  = 10,
    number_of_migrated_agents = 0,
    salinity_shock_step = [125, 191]):

        super().__init__(seed = seed)
        # Set seeds
        self.seed = seed
        random.seed(20)
        np.random.seed(20)

        # Create area
        self.district = district 
        self.data_salinity, self.polygon_districts = self.gather_shapefiles(self.district) 
        self.G = self.initialize_network(self.data_salinity, self.polygon_districts, sum(num_agents.values()), self.seed)
        self.grid = NetworkGrid(self.G)

        # Determine facilities
        self.factory_in_neighborhood = False
        self.factory_advertisement = False

        # Possibility for a shock
        self.salinity_shock_step = salinity_shock_step
        self.salinity_shock = False
        self.time_since_shock = 0

        # Possibility for disease
        self.chance_disease = {"Extensive": 0.16, "Intensive": 0.5, "MS": 0.1}
        self.use_antibiotics = {"Aqua_small_saline": 0.8}

        # Keep track of the wage workers and their income
        self.total_number_ww_aqua = 0
        self.total_number_ww_agri = 0
        self.total_income_aqua_ww = 0
        self.total_income_agri_ww = 0
        self.income_per_aqua_ww = 0
        self.income_per_agri_ww  = 0

        # Keep track of total_population
        self.start_number_of_inhabitants = 0
        self.number_of_inhabitants = 0
        self.reduce_service_income_migrations = 0

        # Chance an agent wants to leave the household
        self.chance_leaving_household = 0.3 # Should be determined later 

        # Income
        self.interest_rate_savings = 0.05
        self.interest_rate_loans = 0.1

        # Set up data collector
        model_metrics = {}
        agent_metrics = {"Agent_type": "agent_type","Age":'ages', "Salinity": 'salinity', "Savings":"savings", "Loan_size": 'loan_size',
        'maximum_debt':"maximum_debt", 'income':'income', 'abilities':'abilities', 'current_crop':'current_crop', "New crop":"new_crop"}
        self.datacollector = DataCollector(model_reporters = model_metrics, agent_reporters = agent_metrics)

        # Create farmer agents
        self.num_agents = num_agents
        available_nodes = list(self.G.nodes())
        random.shuffle(available_nodes)

        agent_classes = { "Agri_small_saline": Agri_small_saline, "Agri_small_fresh": Agri_small_fresh, "Aqua_small_saline": Aqua_small_saline}

        for agent_type, count in num_agents.items():
            AgentClass = agent_classes[agent_type]
            for i in range(count):
                node_id = available_nodes.pop(0)
                salinity = self.G.nodes[node_id]['salinities']
                agent = AgentClass(self, agent_type, node_id, salinity)
                self.agents.add(agent)
                self.grid.place_agent(agent, node_id)

        # Create low skilled wage worker agents
        for work_type, count in num_low_skilled_ww.items():
            for i in range (count):
                low_skilled_ww = Low_skilled_wage_worker(self, work_type)
                self.agents.add(low_skilled_ww)

        # Create service worker agents
        for i in range (num_service_workers):
            service_worker = Service_workers(self, work_type)
            self.agents.add(service_worker)

        # Create migrated agents
        for i in range(number_of_migrated_agents):
            migrated_agent = Migrated(self, agent_type = "migrated")
            self.agents.add(migrated_agent)
    
# HIER IS DE STEP FUNCTIE (voor de blinde mensen zoals ik die elke keer zoeken)
    def step(self):
        self.agents.shuffle_do('step')

        # At the first step, check number of inhabitants. this is the 100% income for the service workers
        if self.steps == 1:
            self.start_number_of_inhabitants = sum(agent.household_size for agent in self.agents if hasattr(agent, 'household_size'))

        # Check if a shock is happening
        self.check_shock()
        self.agents.do(lambda agent: setattr(agent, 'growth_time', agent.growth_time + 1) if isinstance(agent, (Agri_farmer, Aqua_farmer)) else None)


        if self.steps % 12 == 0:

            # All agents should do their yearly activities, except for the migrated agents, they do not have those yet
            self.agents.do(lambda agent: agent.yearly_activities() if not isinstance(agent, Migrated) else None)

            # Give wage workers income, based on the total number of wage workers
            self.update_wage_worker_totals()
            self.calculate_income_ww()

            # Calculate income for service workers if agents migrated
            self.number_of_inhabitants = sum(agent.household_size for agent in self.agents if hasattr(agent, 'household_size'))
            self.reduce_service_income_migrations = self.number_of_inhabitants/self.start_number_of_inhabitants

            # Wage workers should receive income
            self.agents.do(lambda agent:agent.receive_income() if isinstance(agent,(Low_skilled_wage_worker, Service_workers)) else None)

            # Collect data
            self.datacollector.collect(self)

            # total_migrated = sum(1 for agent in self.agents if isinstance(agent, Migrated))
            # print(total_migrated)

            # Set income to zero, to calculate everything new for the next year
            self.agents.do(lambda agent: agent.reset_income() if isinstance(agent, (Agri_farmer, Aqua_farmer)) else None)
      
        # Time to harvest!
        #yieldtime_crops = {"Rice":6, "Mango":12, "Coconut": 12} # THESE ARE NOT REAL NUMBERS YET
        self.agents.do(lambda agent: agent.harvest() if isinstance(agent, (Agri_farmer, Aqua_farmer)) and agent.growth_time == agent.yield_time else None) 


    def gather_shapefiles(self, district):
        # Define path
        path = os.getcwd()

        # Import salinity data and select the correct district, and set meters using epsg
        path_salinity = path + "\\districts_salinity.gpkg"
        gdf_salinity = gpd.read_file(path_salinity)

        gdf_salinity = gdf_salinity[gdf_salinity['District']==district]
        gdf_salinity = gdf_salinity.to_crs(epsg=32648) 

        # Import district boundaries and select correct district, and set to correct epsg
        path_district = path + "\\district_boundaries.gpkg"
        gdf_district_boundaries = gpd.read_file(path_district)

        gdf_district_boundaries = gdf_district_boundaries[gdf_district_boundaries['District']==district]
        gdf_district_boundaries = gdf_district_boundaries.to_crs(epsg=32648) 

        # create polygon for the district boundaries file
        polygon_boundaries = gdf_district_boundaries.unary_union
        district_series = gpd.GeoSeries(polygon_boundaries)

        return gdf_salinity, district_series


    def initialize_network(self, salinity_data, districts_polygon, num_agents, seed):
        
        # Define number of points
        points = districts_polygon.sample_points(size=num_agents, seed = seed)

        points_list = list(points.geometry[0].geoms)
        coords = np.array([(pt.x, pt.y) for pt in points_list])

        # Create a network, three nearest nodes are supposed to be your neighbours
        tree = cKDTree(coords)
        k = 4  
        distances, indices = tree.query(coords, k=k)

        G = nx.Graph()

        # Add nodes
        for i, (x, y) in enumerate(coords):
            point = Point(x,y)

            get_salinity = salinity_data[salinity_data.contains(point)]
            if not get_salinity.empty:
                salinities = get_salinity.iloc[0]['Salinity']
            else:
                salinities = None
                print("dit ging mis")
            G.add_node(i, pos=(x, y), salinities = salinities)

        # Add edges
        for i, neighbors in enumerate(indices):
            for j in neighbors[1:]:  # skip the first one, that is the point itself
                G.add_edge(i, j)

        return G

    def check_shock(self):
        if self.steps in self.salinity_shock_step:
            self.salinity_shock = True
            for agent in self.agents:
                if hasattr(agent, "salinity"):
                    agent.salinity = random.uniform (1.5, 2) * agent.salinity # ASSUMPTION, NEED TO DETERMINE HOW INTENSE A SHOCK IS
                    agent.salinity_during_shock = agent.salinity

            self.time_since_shock = 0
            print("shock is happening!!")

        else:
            self.salinity_shock = False
            self.time_since_shock +=1
            if self.time_since_shock == 1:
                for agent in self.agents:
                    if hasattr(agent, "salinity"):
                        agent.salinity = agent.salinity/random.uniform(1.5, 2) # ASSUMPTION, NEED TO DETERMINE HOW INTENSE A SHOCK IS

    def update_wage_worker_totals(self):
        # Reset totals before each step
        self.total_number_ww_aqua = 0
        self.total_number_ww_agri = 0
        self.total_income_aqua_ww = 0
        self.total_income_agri_ww = 0
        self.income_per_aqua_ww = 0
        self.income_per_agri_ww = 0

        # Count the number of low skilled wage workers in agri and aqua
        for agent in self.agents:
            if isinstance(agent, Low_skilled_wage_worker):
                if agent.agent_type == "Aqua":
                    self.total_number_ww_aqua += agent.working_force
                elif agent.agent_type == "Agri":
                    self.total_number_ww_agri += agent.working_force
                
            if isinstance(agent, Agri_farmer):
                self.total_income_agri_ww += agent.income_spent_on_ww

            # LATER ADD AQUA FARMERS HERE TOO
            # if isinstance(agent, Aqua_farmer):
            #     self.total_income_aqua_ww += agent.income_spent_on_ww

    def calculate_income_ww(self):
        # Count the total income of aqua and agri wage workers, and determine the income per household, based on their working force
        if self.total_number_ww_aqua > 0:
            self.income_per_aqua_ww = self.total_income_aqua_ww / self.total_number_ww_aqua 
            for agent in self.agents:
                if isinstance(agent, Low_skilled_wage_worker) and agent.agent_type == "Aqua":
                    agent.income = self.income_per_aqua_ww * agent.working_force
                    

        if self.total_number_ww_agri > 0:
            self.income_per_agri_ww = self.total_income_agri_ww / self.total_number_ww_agri
            for agent in self.agents:
                if isinstance(agent, Low_skilled_wage_worker) and agent.agent_type == "Agri":
                    agent.income = self.income_per_agri_ww * agent.working_force 
