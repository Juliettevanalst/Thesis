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
import pandas as pd
from mesa import Model, Agent
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
from collections import defaultdict
from shapely.geometry import MultiPoint

from Agents3 import Low_skilled_agri_worker, Low_skilled_nonAgri, Manual_worker, Skilled_agri_worker, Skilled_service_worker, Other, Non_labourer, Small_land_households, Middle_land_households, Large_land_households, Landless_households
# Define path
path = os.getcwd()

# Import data
correct_path = path + "\Data\model_input_data_823.xlsx"

class RiverDeltaModel(Model):
    def __init__(self, seed=20, district = 'Binh Thuy', num_agents = 1000, excel_path =correct_path):
        super().__init__(seed=seed)
        self.seed = seed
        random.seed(20)
        np.random.seed(20)

        # Generate agents
        self.num_agents = num_agents
        self.excel_data = self.get_excel_data(excel_path)
        self.generate_agents()

        # Define area
        self.district = district
        self.data_salinity, self.polygon_districts = self.gather_shapefiles(self.district) 
        households_which_need_a_node = []
        for agent in self.agents:
            if agent.agent_type == "Household" and agent.land_area > 0.0:
                households_which_need_a_node.append(agent)
        self.G = self.initialize_network(self.data_salinity, self.polygon_districts,len(households_which_need_a_node) , self.seed)
        self.grid = NetworkGrid(self.G)
        print(f"Aantal nodes in G: {len(self.G.nodes())}")
        print(f"Voorbeeld nodes: {list(self.G.nodes())[:5]}")

        # Connect farmer households to the grid
        available_nodes = list(self.G.nodes())
        random.shuffle(available_nodes)
        for agent in households_which_need_a_node:
            node_id = available_nodes.pop(0)
            print(node_id)
            salinity_level = self.G.nodes[node_id]["salinities"]
            agent.salinity = salinity_level
            agent.node_id = node_id
            self.grid.place_agent(agent, agent.node_id)

    def generate_agents(self):
        # Create individual agents
        agent_classes = {"low_skilled_agri_worker": Low_skilled_agri_worker, "low_skilled_nonAgri":Low_skilled_nonAgri, "manual_worker":Manual_worker, "other":Other, "skilled_agri_worker":Skilled_agri_worker, "skilled_service_worker": Skilled_service_worker}
        for i in range(self.num_agents):
            age = self.get_age(self.excel_data['age_distribution'])
            works = self.is_working(age, self.excel_data['work_per_agegroup'])

            # If the agent is working: 
            if works == True:
                agent_sector = self.define_sector(self.excel_data['sector_distribution'])
                agent_occupation = self.define_occupation(agent_sector, self.excel_data['occupation_employment_distribution'])
                agent_employment_type = self.define_employment(agent_sector, agent_occupation, self.excel_data['occupation_employment_distribution'])
                assigned = False
                works = True
                agent_type = "Household_member"

                AgentClass = agent_classes[agent_occupation]
                agent = AgentClass(self, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works)
                self.agents.add(agent)
                # NEED TO PLACE AGENT ON THE GRID HERE!!! TO DO 

            # If the agent is not working:
            else:
                AgentClass = Non_labourer
                agent_employment_type = 'Non_labourer'
                assigned = False
                works = False
                agent_type = "Household_member"
                agent = AgentClass(self, agent_type, age, agent_employment_type, assigned, works)
                self.agents.add(agent)

        Household_agent_classes = {"small": Small_land_households, "medium":Middle_land_households, "large": Large_land_households}
        
        # Time to create the farms:
        farm_owner_agents = [agent for agent in self.agents if not agent.assigned and agent.agent_employment_type=='self_employed' and agent.agent_sector != 'Non_agri'] # This is the main farm owners, they start the farm!!

        for agent in farm_owner_agents:
            print("we starten een farm")
            if agent.assigned == True:
                continue
            # Define household size
            household_size = max(1, int(self.random.normalvariate(self.excel_data['household_size']['mean'],self.excel_data['household_size']['std_dev'])))
            main_crop = agent.agent_sector
            # Define land size
            land_category = self.sample_from_distribution(self.excel_data['land_sizes'])
            land_area = self.get_land_area(land_category)
            salinity = 0
            node_id = 0
            # Check housing situation
            house_quality = self.get_house_quality()
            # Add household_member to the household:
            household_members = [agent]
            agent_type = "Household"

            agent.assigned = True

            # Add possible self agri workers
            land_statistics = self.excel_data['work_type_per_land_size'][agent.agent_sector][land_category]
            desired_self_agri = self.number_of_members_per_type(land_statistics['Worked_self_agri'])
            self.add_similar_agents_to_household(household_members, count=desired_self_agri - 1, sector=agent.agent_sector,employment_type="family_worker") # Family workers work on the farm of the main farm owner

            # Add possible other workers (wage and self non agri)
            desired_self_nonagri = self.number_of_members_per_type(land_statistics['Worked_self_nonAgri'])
            desired_wage = self.number_of_members_per_type(land_statistics['Worked_wage'])
            self.add_similar_agents_to_household(household_members, count=desired_self_nonagri,sector="non_agri") # Add self non agri people
            self.add_similar_agents_to_household(household_members, count=desired_wage,employment_type="employee") # Add non family workers

            # Add eldery/children until household is full 
            while len(household_members) < household_size:
                unassigned = [a for a in self.agents if a.agent_type == "Household_member" and not a.assigned and not a.works]
                if not unassigned:
                    break

                new_member = self.random.choice(unassigned)
                new_member.assigned = True
                household_members.append(new_member)

            # Create household
            AgentClass = Household_agent_classes[land_category]
            household = AgentClass(self, agent_type, household_size, household_members, land_category, land_area, house_quality, salinity, main_crop, node_id)
            self.agents.add(household)

        # Time to create landless households
        unassigned_agents = [a for a in self.agents if a.agent_type == "Household_member" and not a.assigned]
        self.random.shuffle(unassigned_agents)

        while True:
            age_groups = self.get_unassigned_by_age_group(unassigned_agents)

            if not age_groups["adults"]:
                break

            # Define household size
            household_size = max(1,int(self.random.normalvariate(float(self.excel_data['household_size']['mean']),float(self.excel_data['household_size']['std_dev']))))

            # Each household should have minimal 1 adult
            adult = age_groups["adults"].pop()
            adult.assigned = True
            household_members = [adult]
            unassigned_agents.remove(adult)

            # Add other family members
            needed = household_size - 1
            for group in ["children", "elderly", "adults"]:  
                while needed > 0 and age_groups[group]:
                    member = age_groups[group].pop()
                    member.assigned = True
                    household_members.append(member)
                    unassigned_agents.remove(member)
                    needed -= 1

            # Define house quality
            house_quality = self.get_house_quality()
            land_area = 0
            agent_type = "Household"
            AgentClass = Landless_households
            household = AgentClass(self, agent_type, household_size, household_members, land_area, house_quality)
            self.agents.add(household)

        # print number of unassigned agents
        unassigned_agents = [a for a in self.agents if hasattr(a, 'agent_type') and a.agent_type == "Household_member" and not a.assigned]
        print("There are", len(unassigned_agents), "agents unassigned!!")

    def step(self):
        print("HET WERKT!!!")
        self.agents.shuffle_do('step')

    def sample_from_distribution(self, land_sizes):
        print("we komen hier")
        chance_land_size = self.random.random()
        for key, (low, high) in land_sizes.items():
            if low <= chance_land_size <= high:
                return key

    def get_land_area(self, land_category):
        if land_category == "small":
            return self.random.uniform(0, 0.5)
        elif land_category == "medium":
            return self.random.uniform(0.5, 2)
        elif land_category == "large":
            return self.random.uniform(2, 5)  
        return 0

    def get_unassigned_by_age_group(self, unassigned_agents):
        number_people = {"children": [], "adults": [], "elderly": []}
        for agent in unassigned_agents:
            if agent.age <= 15:
                number_people["children"].append(agent)
            elif 16 <= agent.age <= 64:
                number_people["adults"].append(agent)
            else:
                number_people["elderly"].append(agent)
        return number_people
  
    def get_house_quality(self):
        mean = self.excel_data['housing_quality']['mean']
        std = self.excel_data['housing_quality']['std_dev']
        return min(1.0, max(0.0, self.random.normalvariate(mean, std)))

    def number_of_members_per_type(self, number):
        int_number = int(number)
        if self.random.random() < (number - int_number):
            return int_number + 1
        else:
            return int_number

    def add_similar_agents_to_household(self, household, count, sector=None, employment_type=None):
        possible_agents = [a for a in self.agents if a.agent_type == "Household_member" and not a.assigned and (getattr(a, 'agent_sector', None) is None or a.agent_sector == sector) and (employment_type is None or getattr(a, 'agent_employment_type', None) == employment_type)]
        self.random.shuffle(possible_agents)
        for a in possible_agents[:count]:
            a.assigned = True
            household.append(a)

    def get_age(self, age_distribution):
        chance_age = self.random.random()
        cumulative = 0
        for (low, high), probability in age_distribution.items():
            cumulative += probability
            if chance_age <= cumulative:
                age = self.random.randint(low, high)
                return age

    def is_working(self, age, work_per_agegroup):
        for (low, high), chance in work_per_agegroup.items():
            if low <= age <= high:
                return self.random.random() < chance
        return False

    def define_sector(self, sector_distribution):
        chance_sector = self.random.random()
        for sector, (low, high) in sector_distribution.items():
            if low <= chance_sector <= high:
                agent_sector = sector
                return agent_sector

    def define_occupation(self, agent_sector, occupation_distribution):
        occupations = occupation_distribution[agent_sector]
        chance_occupation = self.random.random()
        cumulative = 0
        for occupation, probabilities in occupations.items():
            probability = probabilities['occupation_probability']
            cumulative += probability
            if chance_occupation <= cumulative:
                agent_occupation = occupation
                return agent_occupation

    def define_employment(self, agent_sector, agent_occupation, employment_distribution): 
        employment_types = employment_distribution[agent_sector][agent_occupation]['employment_distribution']
        chance_employment = self.random.random()
        cumulative = 0
        for employment_type, probability in employment_types.items():
            cumulative += probability
            if chance_employment <= cumulative:
                agent_employment = employment_type
                return agent_employment


    def get_excel_data(self,excel_path):
        sheets = pd.read_excel(excel_path, sheet_name = None)

        return {
        'age_distribution': self.process_age_distribution(sheets['age_distribution']),
        'work_per_agegroup': self.process_work_per_agegroup(sheets['Percent_working_per_age']),
        'sector_distribution': self.process_sector_distribution(sheets['Sector_distribution']),
        'occupation_employment_distribution':self.process_occupation_employment_distribution(sheets['Occupation_and_employment']),
        'household_size': self.process_household_size(sheets['Household_size']),
        'land_sizes': self.process_land_sizes(sheets['Land_sizes']),
        'work_type_per_land_size': self.process_work_type_per_land_size(sheets['Work_type_per_land_size']),
        'housing_quality': self.process_housing_quality(sheets['Housing_quality'])

    }

    def process_age_distribution(self, df):
        age_dist = {}
        for i, row in df.iterrows():
            low, high = map(int, row['age_group'].split('-'))
            age_dist[(low, high)] = row['percentage']
        return age_dist

    def process_work_per_agegroup(self, df):
        work_dict = {}
        for i, row in df.iterrows():
            low, high = map(int, row['age_group'].split('-'))
            work_dict[(low, high)] = row['working'] / 100
        return work_dict

    def process_sector_distribution(self, df):
        sector_dict = {}
        cumulative = 0
        for i, row in df.iterrows():
            prob = row['Probability']
            sector = row['Sector']
            sector_dict[sector] = (cumulative, cumulative + prob)
            cumulative += prob
        return sector_dict

    # def process_occupation_distribution(self, df):
    #     sector_occupations = defaultdict(dict)
    #     for i, row in df.iterrows():
    #         sector = row['Sector']
    #         occupation = row['Occupation']
    #         probability = row['perc_occupation']
    #         sector_occupations[sector][occupation] = probability
    #     return sector_occupations

    # def process_employment_distribution(self, df):
    #     employment_dist = defaultdict(dict)
    #     for i, row in df.iterrows():
    #         sector = row['Sector']
    #         employment_dist[sector]['family_worker'] = row['Family_worker'] / 100  # Zorg dat het een kans is (0–1)
    #         employment_dist[sector]['other'] = row['Other'] / 100
    #     return employment_dist

    def process_occupation_employment_distribution(self, df):
        occupation_dict = defaultdict(lambda: defaultdict(dict))
    
        for i, row in df.iterrows():
            sector = row['Sector']
            occupation = row['Occupation']
            occupation_dict[sector][occupation]['occupation_probability'] = row['perc_occupation'] / 100  
            occupation_dict[sector][occupation]['employment_distribution'] = {'family_worker': row['Family_worker'] / 100,'self_employed': row['Other']/100, "employee": row['Employee'] / 100}
        return occupation_dict
    

    def process_household_size(self, df):
        mean = float(df[df.iloc[:, 0] == 'mean'].iloc[0, 1])
        std_dev = float(df[df.iloc[:, 0] == 'std_dev'].iloc[0, 1])
        return {'mean': mean,'std_dev': std_dev}
        
    def process_land_sizes(self, df):
        size_probabilities = {}
        cumulative = 0
        for i, row in df.iterrows():
            cat = row['land_size_type']
            prob = row['percentage']
            size_probabilities[cat] = (cumulative, cumulative + prob)
            cumulative += prob
        return size_probabilities

    def process_work_type_per_land_size(self, df):
        land_dict = defaultdict(dict)
        for i, row in df.iterrows():
            sector = row['Dominant_income_source']
            land_cat = row['land_size_type']
            land_dict[sector][land_cat] = {
                'Worked_self_agri': row['Worked_self_agri'],
                'Worked_self_nonAgri': row['Worked_self_nonAgri'],
                'Worked_wage': row['Worked_wage']}
        return land_dict

    def process_housing_quality(self, df):
        df = df.set_index('hh_quality')
        return {'mean': df.loc['mean', 'value'],'std_dev': df.loc['std_dev', 'value']}

    def gather_shapefiles(self, district):
        path = os.getcwd()

        # Import salinity data and select the correct district, and set meters using epsg
        path_salinity = path + "\\Data\districts_salinity.gpkg"
        gdf_salinity = gpd.read_file(path_salinity)

        gdf_salinity = gdf_salinity[gdf_salinity['District']==self.district]
        gdf_salinity = gdf_salinity.to_crs(epsg=32648) 

        # Import district boundaries and select correct district, and set to correct epsg
        path_district = path + "\\Data\district_boundaries.gpkg"
        gdf_district_boundaries = gpd.read_file(path_district)

        gdf_district_boundaries = gdf_district_boundaries[gdf_district_boundaries['Ten_Huyen']==self.district]
        gdf_district_boundaries = gdf_district_boundaries.to_crs(epsg=32648) 

        # create polygon for the district boundaries file
        polygon_boundaries = gdf_district_boundaries.unary_union
        district_series = gpd.GeoSeries(polygon_boundaries)

        return gdf_salinity, district_series

    def initialize_network(self, salinity_data, districts_polygon, land_agents, seed):
        
        # Define number of points
        points = districts_polygon.sample_points(size=land_agents, seed = seed)

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





            





