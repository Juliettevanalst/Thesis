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
from statistics import mean

from Agents3 import Low_skilled_agri_worker, Low_skilled_nonAgri, Manual_worker, Skilled_agri_worker, Skilled_service_worker
from Agents3 import Other, Non_labourer, Small_land_households, Middle_land_households, Large_land_households, Landless_households
from Agents3 import Land_household, Working_hh_member, Migrated_household, Migrated_hh_member

# Define path
path = os.getcwd()

# Import data
correct_path = path + "\\Data\\model_input_data_823.xlsx"


class RiverDeltaModel(Model):
    def __init__(
        self,
        seed=20,
        district='Gò Công Tây',
        num_agents=1000,
        excel_path=correct_path,
        salinity_shock_step=[
            114,
            191]):
        super().__init__(seed=seed)
        self.seed = seed
        random.seed(20)
        np.random.seed(20)

        # Generate agents
        self.num_agents = num_agents
        self.excel_data = self.get_excel_data(excel_path)
        self.generate_agents()
        self.death_agents = 0

        # Define area
        self.district = district
        self.data_salinity, self.polygon_districts = self.gather_shapefiles(
            self.district)
        households_which_need_a_node = []
        for agent in self.agents:
            if agent.agent_type == "Household" and agent.land_area > 0.0:
                households_which_need_a_node.append(agent)
        self.G = self.initialize_network(
            self.data_salinity,
            self.polygon_districts,
            len(households_which_need_a_node),
            self.seed)
        self.grid = NetworkGrid(self.G)

        # Connect farmer households to the grid
        available_nodes = list(self.G.nodes())
        random.shuffle(available_nodes)
        for agent in households_which_need_a_node:
            node_id = available_nodes.pop(0)
            salinity_level = self.G.nodes[node_id]["salinities"]
            agent.salinity = salinity_level
            agent.node_id = node_id
            self.grid.place_agent(agent, agent.node_id)

        # Possibility for a shock
        self.salinity_shock_step = salinity_shock_step
        self.salinity_shock = False
        self.time_since_shock = 0

        # Does the agent meet agrocensus?
        self.chance_info_meeting = 0.1  # Based on paper by Tran et al, (2020)

        # Possibility for disease
        # Based on paper by Joffre et al., 2015 on extensive shrimp farming
        self.chance_disease = 0.16

        # Maize costs
        self.maize_fixed_costs = 3400000 # Based on paper by Ba et al., (2017)

        # possibility for migration
        self.chances_migration = [0.03, 0.01, 0.01, 0.005, 0.01, 0.005] # THESE ARE RANDOM
        self.chance_leaving_household = 0.05  # ASSUMPTION
        self.increased_chance_migration_familiarity = 0.1

        # Interest rates for loans and savings
        self.interest_rate_loans = 0.1
        self.interest_rate_savings = 0.05

        # Distribution man_days during preparation time and yield time
        self.man_days_prep = 1 / 3
        # ASSUMPTION, average / day is 200000 based on Pedroso et al., 2017
        self.payment_low_skilled = 190000
        # ASSUMPTION, average / day is 200000 based on Pedroso et al., 2017
        self.payment_high_skilled = 210000
        self.distribution_high_low_skilled = 0  # Need to define later

        # Number of deceased households (all household members have died)
        self.deceased_households = 0
        self.child_births = 0
        self.death_household_members = 0

        # Number_of_households
        self.number_of_households = 0
        for agent in self.agents:
            if agent.agent_type == "Household":
                self.number_of_households += 1

        self.start_households = self.number_of_households
        self.current_hh_left = self.number_of_households
        self.agents_to_remove = []
        self.agents_become_manual = []
        self.agents_become_low_skilled_farm = []
        self.agents_become_migrated_members = []

        # number of workers
        self.start_total_low_nonagri = len([agent for agent in self.agents if hasattr(
            agent, 'agent_occupation') and agent.agent_type == "Household_member" and agent.agent_occupation == "low_skilled_nonAgri"])
        self.work_days_per_week = 20
        self.start_manual_other_workers = len(
            [
                agent for agent in self.agents if agent.agent_type == "Household_member" and hasattr(
                    agent, 'agent_occupation') and (
                    agent.agent_occupation == "manual_worker" or agent.agent_occupation == "other")])
        self.start_service_workers = len(
            [
                agent for agent in self.agents if agent.agent_type == "Household_member" and hasattr(
                    agent,
                    'agent_occupation') and agent.agent_occupation == "skilled_service_worker"])
        self.current_service_workers = self.start_service_workers

        # Set up datacollector
        model_metrics = {
            "Average_Livelihood": lambda model: mean(
                [
                    agent.livelihood['Average'] for agent in self.agents if hasattr(
                        agent,
                        'livelihood')]) if self.agents else 0,
                        
                        "Num_household_members":lambda model: sum(1 for agent in model.agents if getattr(agent, "agent_type", None)== "Household_member"),
                        "Migrated_households": lambda model: sum(1 for agent in model.agents if getattr(agent, "agent_type", None)=="Migrated"),
                        "Migrated_members": lambda model: sum(1 for agent in model.agents if getattr(agent, "agent_type", None)=="Migrated_member"),
                        "Migrated_individuals": lambda model: sum(1 for agent in model.agents if getattr(agent, "agent_type", None)=="Migrated_member_young_adult"),
                        "Died agents":lambda model: self.death_agents,
                        "Child births":lambda model: self.child_births
                        }
        agent_metrics = {"Crop_type": lambda a: getattr(a, "crop_type", None) if getattr(a, "agent_type", None)=="Household" else None,
                        "Land_category":lambda a: getattr(a, "land_category", None) if getattr(a, "agent_type", None)=="Household" else None,
                        "Savings": lambda a: getattr(a, "savings", None) if getattr(a, "agent_type", None)== "Household" else None,
                        "too low income": lambda a: getattr(a, "income_too_low", None) if hasattr(a, "income_too_low" ) else None}
        self.datacollector = DataCollector(
            model_reporters=model_metrics,
            agent_reporters=agent_metrics)

    def generate_agents(self):
        # Create individual agents
        agent_classes = {
            "low_skilled_agri_worker": Low_skilled_agri_worker,
            "low_skilled_nonAgri": Low_skilled_nonAgri,
            "manual_worker": Manual_worker,
            "other": Other,
            "skilled_agri_worker": Skilled_agri_worker,
            "skilled_service_worker": Skilled_service_worker}
        for i in range(self.num_agents):
            age = self.get_age(self.excel_data['age_distribution'])
            works = self.is_working(age, self.excel_data['work_per_agegroup'])

            # If the agent is working:
            if works:
                agent_sector = self.define_sector(
                    self.excel_data['sector_distribution'])
                agent_occupation = self.define_occupation(
                    agent_sector, self.excel_data['occupation_employment_distribution'])
                agent_employment_type = self.define_employment(
                    agent_sector,
                    agent_occupation,
                    self.excel_data['occupation_employment_distribution'])
                assigned = False
                works = True
                agent_type = "Household_member"

                AgentClass = agent_classes[agent_occupation]
                agent = AgentClass(
                    self,
                    agent_type,
                    age,
                    agent_sector,
                    agent_occupation,
                    agent_employment_type,
                    assigned,
                    works)
                self.agents.add(agent)
                # NEED TO PLACE AGENT ON THE GRID HERE!!! TO DO

            # If the agent is not working:
            else:
                AgentClass = Non_labourer
                agent_employment_type = 'Non_labourer'
                assigned = False
                works = False
                agent_type = "Household_member"
                agent = AgentClass(
                    self,
                    agent_type,
                    age,
                    agent_employment_type,
                    assigned,
                    works)
                self.agents.add(agent)

        Household_agent_classes = {
            "small": Small_land_households,
            "medium": Middle_land_households,
            "large": Large_land_households}

        # Time to create the farms:
        farm_owner_agents = [agent for agent in self.agents if not agent.assigned and agent.agent_employment_type ==
                             'self_employed' and agent.agent_sector != 'Non_agri']  # This is the main farm owners, they start the farm!!

        for agent in farm_owner_agents:
            if agent.assigned:
                continue
            # Define household size
            household_size = max(
                1, int(
                    self.random.normalvariate(
                        self.excel_data['household_size']['mean'], self.excel_data['household_size']['std_dev'])))
            crop_type = agent.agent_sector
            # Define land size
            land_category = self.sample_from_distribution(
                self.excel_data['land_sizes'])
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
            desired_self_agri = self.number_of_members_per_type(
                land_statistics['Worked_self_agri'])
            self.add_similar_agents_to_household(
                household_members,
                count=desired_self_agri - 1,
                sector=agent.agent_sector,
                employment_type="family_worker")  # Family workers work on the farm of the main farm owner

            # Add possible other workers (wage and self non agri)
            desired_self_nonagri = self.number_of_members_per_type(
                land_statistics['Worked_self_nonAgri'])
            desired_wage = self.number_of_members_per_type(
                land_statistics['Worked_wage'])
            self.add_similar_agents_to_household(
                household_members,
                count=desired_self_nonagri,
                sector="non_agri")  # Add self non agri people
            self.add_similar_agents_to_household(
                household_members,
                count=desired_wage,
                employment_type="employee")  # Add non family workers

            # Add eldery/children until household is full
            while len(household_members) < household_size:
                unassigned = [a for a in self.agents if a.agent_type ==
                              "Household_member" and not a.assigned and not a.works]
                if not unassigned:
                    break

                new_member = self.random.choice(unassigned)
                new_member.assigned = True
                household_members.append(new_member)

            # Create household
            AgentClass = Household_agent_classes[land_category]
            household = AgentClass(
                self,
                agent_type,
                household_size,
                household_members,
                land_category,
                land_area,
                house_quality,
                salinity,
                crop_type,
                node_id)
            for member in household_members:
                member.household = household
            self.agents.add(household)

        # Time to create landless households
        unassigned_agents = [
            a for a in self.agents if a.agent_type == "Household_member" and not a.assigned]
        self.random.shuffle(unassigned_agents)

        while True:
            age_groups = self.get_unassigned_by_age_group(unassigned_agents)

            if not age_groups["adults"]:
                break

            # Define household size
            household_size = max(
                1, int(
                    self.random.normalvariate(
                        float(
                            self.excel_data['household_size']['mean']), float(
                            self.excel_data['household_size']['std_dev']))))

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

            # Create household agent
            AgentClass = Landless_households
            household = AgentClass(
                self,
                agent_type,
                household_size,
                household_members,
                land_area,
                house_quality)
            for member in household_members:
                member.household = household
            self.agents.add(household)

        # print number of unassigned agents
        unassigned_agents = [a for a in self.agents if hasattr(
            a, 'agent_type') and a.agent_type == "Household_member" and not a.assigned]
        print("There are", len(unassigned_agents), "agents unassigned!!")

    def step(self):
        self.agents.shuffle_do('step')

        self.number_of_households = 0
        for agent in self.agents:
            if hasattr(agent, "time_since_last_income"):
                agent.time_since_last_income += 1
            if agent.agent_type == "Household":
                self.number_of_households += 1

        self.current_hh_left = self.number_of_households / self.start_households

        # Check if a shock is happening
        self.check_shock()

        # Print total number of agents
        number_of_hh_members = 0
        for agent in self.agents:
            if agent.agent_type == "Household_member":
                number_of_hh_members += 1
        print(number_of_hh_members)

        # Decrease waiting_time
        for agent in self.agents: 
            if hasattr(agent, "waiting_time_"):
                for key in agent.waiting_time_:
                    if agent.waiting_time_[key] > 0:
                        agent.waiting_time_[key] -= 1

        if self.steps % 12 == 0:
            self.agents.do(
                lambda agent: agent.yearly_activities() if isinstance(
                    agent,
                    (Working_hh_member,
                     Land_household,
                     Landless_households,
                     Non_labourer)) else None)
            self.need_to_yield(["Rice", "Coconut"])
            self.agents.do(lambda agent: agent.update_experience() if isinstance(
                agent, Land_household) else None)
            self.pay_wage_workers()
            self.pay_other_agents()
            self.check_class_switches()

        month = self.steps % 12

        if month == 2:
            self.need_to_yield(["Rice", "Coconut"])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.check_class_switches()

        elif month == 4:
            self.need_to_yield(["Coconut", "Maize", "Shrimp"])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.pay_other_agents()
            self.check_class_switches()

        elif month == 6:
            self.need_to_yield(['Coconut'])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.check_class_switches()

        elif month == 8:
            self.need_to_yield(["Rice", "Maize", 'Coconut'])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.pay_other_agents()
            self.check_class_switches()

        elif month == 10:
            self.need_to_yield(["Shrimp", 'Coconut'])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.check_class_switches()

        elif month == 11:
            self.need_to_yield(["Rice"])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.check_class_switches()

        if self.steps % 12 == 0:
            # Collect data
            self.datacollector.collect(self)

    def need_to_yield(self, crop_type):
        for crop in crop_type:
            for agent in self.agents:
                if isinstance(agent, Land_household):
                    if crop in agent.crops_and_land.keys() and agent.waiting_time_[crop] == 0:
                        agent.harvest(crop)
                        agent.wage_worker_payment = 1
                    else:
                        agent.wage_worker_payment = 0

    def pay_wage_workers(self):
        # Pay farm wage workers:
        selected_agents = [
            agent for agent in self.agents if agent.agent_type == "Household_member" and getattr(
                agent, 'agent_employment_type', None) == "employee" and hasattr(
                agent, 'agent_sector') and agent.agent_sector != "Non_agri"]
        sum_low_skilled = sum(1 for agent in selected_agents if getattr(
            agent, 'agent_occupation', None) == "low_skilled_agri_worker")
        sum_high_skilled = sum(1 for agent in selected_agents if getattr(
            agent, 'agent_occupation', None) == "skilled_agri_worker")
        if sum_low_skilled == 0 and sum_high_skilled == 0:
            print("niemand wil op de farm werken")
            self.distribution_high_low_skilled = 0
        else:
            self.distribution_high_low_skilled = sum_low_skilled / \
                (sum_low_skilled + sum_high_skilled)

        # Check total days wage workers were needed to define number of work
        # days for the wage workers
        total_days_ww_used = sum(
            agent.household_size for agent in self.agents if isinstance(
                agent, Land_household) and agent.wage_worker_payment == 1)
        total_ww = sum_low_skilled + sum_high_skilled

        work_days_per_ww = total_days_ww_used / total_ww
        for agent in selected_agents:
            if agent.agent_occupation == "low_skilled_agri_worker":
                agent.income += self.payment_low_skilled * work_days_per_ww
            elif agent.agent_occupation == "skilled_agri_worker":
                agent.income += self.payment_high_skilled * work_days_per_ww

    def farmers_check_situation(self):
        # alle farm household agents die nu yield hebben gehad checken hun
        # savings en kijken of iets moet veranderen!!
        for agent in self.agents:
            if isinstance(agent, Land_household):
                if agent.wage_worker_payment == 1:
                    agent.check_savings()
                    agent.check_changes()

    def pay_other_agents(self):
        # Pay Low skilled non agri workers and other workers
        selected_agents = [
            agent for agent in self.agents if hasattr(
                agent,
                'agent_occupation') and agent.agent_type == "Household_member" and agent.agent_occupation == "low_skilled_nonAgri"]
        total_low_skilled_nonagri = len(selected_agents)
        for agent in selected_agents:
            income_increase = self.start_total_low_nonagri / total_low_skilled_nonagri
            agent.income += income_increase * 4 * self.payment_low_skilled * \
                self.work_days_per_week  # BIG ASSUMPTION, THAT PEOPLE WORK 20 DAYS/MONTH

        # Pay manual workers and "other" occupation
        selected_agents = [
            agent for agent in self.agents if agent.agent_type == "Household_member" and hasattr(
                agent, 'agent_occupation') and (
                agent.agent_occupation == "manual_worker" or agent.agent_occupation == "other")]
        total_manual_other_workers = len(selected_agents)
        for agent in selected_agents:
            income_increase = self.start_manual_other_workers / total_manual_other_workers
            # They get paid between the high and low skilled income
            income = (self.payment_low_skilled + self.payment_high_skilled) / 2
            agent.income += income_increase * 4 * income * self.work_days_per_week

        # Pay for service workers
        selected_agents = [
            agent for agent in self.agents if agent.agent_type == "Household_member" and hasattr(
                agent, 'agent_occupation') and agent.agent_occupation == "skilled_service_worker"]
        total_service_workers = len(selected_agents)
        self.current_service_workers = total_service_workers
        # Income increase is caused by decrease in other service workers
        increase_in_income = self.start_service_workers / total_service_workers

        # Decrease is caused by decrease in total number of agents
        decrease_in_income = self.current_hh_left
        for agent in selected_agents:
            agent.income += increase_in_income * decrease_in_income * \
                4 * self.payment_high_skilled * self.work_days_per_week

        # Agents need to update their income and see if it is sufficient
        for agent in self.agents:
            if hasattr(agent, 'check_income'):
                agent.check_income(4)

    def check_class_switches(self):
        # There are four type of switches: agents_to_remove = households who are migrating as a whole
        # self.agents_become_manual = are household members who switch from low skilled agri work to manual work
        # self.agents_become_low_skilled_farm = are household members who switch from manual/other work to low skilled agri work
        # self.agents_become_migrated_members = household members between 15
        # and 35 who want to migrate and leave the household

        # If agents migrate, create migrated agents and remove household agents
        for household in self.agents_to_remove:
            migrated_hh = Migrated_household(
                self, agent_type="Migrated", household_members=household.household_members)
            self.agents.add(migrated_hh)
            for household_members in household.household_members:
                migrated_member = Migrated_hh_member(
                    self, agent_type="Migrated_member", household=household_members.household)
                self.agents.add(migrated_member)
                # Remove old agent
                self.agents.discard(household_members)
            # Remove the whole household
            self.agents.discard(household)
        self.agents_to_remove = []

        for household_member in self.agents_become_manual:
            household = household_member.household

            # Add new agent
            manual_worker = Manual_worker(
                self,
                agent_type="Household_member",
                age=household_member.age,
                agent_sector="Non_agri",
                agent_occupation="manual_worker",
                agent_employment_type="employee",
                assigned=True,
                works=True)
            self.agents.add(manual_worker)
            manual_worker.household = household

            # Remove old agent:
            self.agents.discard(household_member)

        self.agents_become_manual = []

        for household_member in self.agents_become_low_skilled_farm:
            household = household_member.household

            # Add new agent
            low_skilled_farm = Low_skilled_agri_worker(
                self,
                agent_type="Household_member",
                age=household_member.age,
                agent_sector="Non_agri",
                agent_occupation="manual_worker",
                agent_employment_type="employee",
                assigned=True,
                works=True)
            self.agents.add(low_skilled_farm)
            low_skilled_farm.household = household

            # Remove old agent
            self.agents.discard(household_member)

        self.agents_become_low_skilled_farm = []

        for household_member in self.agents_become_migrated_members:
            # Add new agent
            migrated_member = Migrated_hh_member(
                self, agent_type="Migrated_member_young_adult", household=household_member.household)
            self.agents.add(migrated_member)

            # Remove old agent:
            self.agents.discard(household_member)

        self.agents_become_migrated_members = []

    def check_shock(self):
        if self.steps in self.salinity_shock_step:
            self.salinity_shock = True
            for agent in self.agents:
                if hasattr(agent, "salinity"):
                    # ASSUMPTION, NEED TO DETERMINE HOW INTENSE A SHOCK IS
                    agent.salinity = self.random.uniform(
                        1.5, 2) * agent.salinity
                    agent.salinity_during_shock = agent.salinity
                if hasattr(agent, "salt_experience"):
                    # ASSUMPTION, SALT EXPERIENCE INCREASES BY 0.2 with a
                    # maximum value of 1
                    agent.salt_experience = min(agent.salt_experience + 0.2, 1)

            self.time_since_shock = 0
            print("shock is happening!!")

        else:
            self.salinity_shock = False
            self.time_since_shock += 1
            if self.time_since_shock == 1:
                for agent in self.agents:
                    if hasattr(agent, "salinity"):
                        # ASSUMPTION, NEED TO DETERMINE HOW INTENSE A SHOCK IS
                        agent.salinity = agent.salinity / \
                            random.uniform(1.5, 2)

    def sample_from_distribution(self, land_sizes):
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

    def add_similar_agents_to_household(
            self,
            household,
            count,
            sector=None,
            employment_type=None):
        possible_agents = [
            a for a in self.agents if a.agent_type == "Household_member" and not a.assigned and (
                getattr(
                    a,
                    'agent_sector',
                    None) is None or a.agent_sector == sector) and (
                employment_type is None or getattr(
                    a,
                    'agent_employment_type',
                    None) == employment_type)]
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

    def define_employment(
            self,
            agent_sector,
            agent_occupation,
            employment_distribution):
        employment_types = employment_distribution[agent_sector][agent_occupation]['employment_distribution']
        chance_employment = self.random.random()
        cumulative = 0
        for employment_type, probability in employment_types.items():
            cumulative += probability
            if chance_employment <= cumulative:
                agent_employment = employment_type
                return agent_employment

    def get_excel_data(self, excel_path):
        sheets = pd.read_excel(excel_path, sheet_name=None)

        return {
            'age_distribution': self.process_age_distribution(sheets['age_distribution']),
            'work_per_agegroup': self.process_work_per_agegroup(sheets['Percent_working_per_age']),
            'sector_distribution': self.process_sector_distribution(sheets['Sector_distribution']),
            'occupation_employment_distribution': self.process_occupation_employment_distribution(
                sheets['Occupation_and_employment']),
            'household_size': self.process_household_size(sheets['Household_size']),
            'land_sizes': self.process_land_sizes(sheets['Land_sizes']),
            'work_type_per_land_size': self.process_work_type_per_land_size(sheets['Work_type_per_land_size']),
            'housing_quality': self.process_housing_quality(sheets['Housing_quality']),
            'population_statistics': self.process_population_statistics(sheets['Statistics_population_size']),
            'education_levels': self.process_education_levels(sheets['Education_level']),
            'experience_occupation': self.process_experience(sheets['Experience_per_occupation']),
            'dissabilities': self.process_dissabilities(sheets['Dissabilities']),
            'association': self.process_association(sheets['Member_association'])}

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
            occupation_dict[sector][occupation]['employment_distribution'] = {
                'family_worker': row['Family_worker'] / 100,
                'self_employed': row['Other'] / 100,
                "employee": row['Employee'] / 100}
        return occupation_dict

    def process_household_size(self, df):
        mean = float(df[df.iloc[:, 0] == 'mean'].iloc[0, 1])
        std_dev = float(df[df.iloc[:, 0] == 'std_dev'].iloc[0, 1])
        return {'mean': mean, 'std_dev': std_dev}

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
        return {'mean': df.loc['mean', 'value'],
                'std_dev': df.loc['std_dev', 'value']}

    def process_population_statistics(self, df):
        statistics_population = dict(zip(df["Statistic"], df["Value"]))
        return statistics_population

    def process_education_levels(self, df):
        education_dict = defaultdict(dict)
        df.reset_index()
        for i, row in df.iterrows():
            low, high = map(int, row['age_group'].split('-'))
            education_dict[(
                low, high)]['Higher_secondary'] = row['Higher Secondary and above'] / 100
            education_dict[(low, high)
                           ]['lower_secondary'] = row['Lower Secondary'] / 100
            education_dict[(low, high)
                           ]['below_primary'] = row['below primary'] / 100
            education_dict[(
                low, high)]['no_schooling'] = row['child or no schooling'] / 100
            education_dict[(low, high)
                           ]['primary_education'] = row['primary'] / 100

        return education_dict

    def process_experience(self, df):
        experience_dict = defaultdict(dict)
        df.reset_index()

        for i, row in df.iterrows():
            occupation = row['Occupation']
            experience = row['3+Experience'] / 100
            machines = row['Machines_equip'] / 100
            experience_dict[occupation] = {
                'Experience': experience, 'Machines': machines}

        return experience_dict

    def process_dissabilities(self, df):
        dissabilities_dict = defaultdict(dict)
        df.reset_index(drop=True, inplace=True)

        for i, row in df.iterrows():
            function = row['function']
            if pd.isna(function):
                if last_function is not None:
                    function = last_function
            for age_group in ['0-15', '16-45', '46-59', '59-85']:
                low, high = map(int, row['age_group'].split('-'))

                dissabilities_dict[(low,
                                    high)][function] = {'No_difficulty': row['No_difficulty'] / 100,
                                                        'Unable': row['Unable'] / 100,
                                                        'Some_difficulty': row['Some_difficulty'] / 100,
                                                        'Very_difficulty': row['Very_difficulty'] / 100}
                last_function = function
        return dissabilities_dict

    def process_association(self, df):
        for i, row in df.iterrows():
            if row['Association'] == "yes":
                percentage_association = row['Percentage']
        return percentage_association

    def gather_shapefiles(self, district):
        path = os.getcwd()

        # Import salinity data and select the correct district, and set meters
        # using epsg
        path_salinity = path + "\\Data\\districts_salinity.gpkg"
        gdf_salinity = gpd.read_file(path_salinity)

        gdf_salinity = gdf_salinity[gdf_salinity['District'] == self.district]
        gdf_salinity = gdf_salinity.to_crs(epsg=32648)

        # Import district boundaries and select correct district, and set to
        # correct epsg
        path_district = path + "\\Data\\district_boundaries.gpkg"
        gdf_district_boundaries = gpd.read_file(path_district)

        gdf_district_boundaries = gdf_district_boundaries[
            gdf_district_boundaries['Ten_Huyen'] == self.district]
        gdf_district_boundaries = gdf_district_boundaries.to_crs(epsg=32648)

        # create polygon for the district boundaries file
        polygon_boundaries = gdf_district_boundaries.unary_union
        district_series = gpd.GeoSeries(polygon_boundaries)

        return gdf_salinity, district_series

    def initialize_network(
            self,
            salinity_data,
            districts_polygon,
            land_agents,
            seed):

        # Define number of points
        points = districts_polygon.sample_points(size=land_agents, seed=seed)

        points_list = list(points.geometry[0].geoms)
        coords = np.array([(pt.x, pt.y) for pt in points_list])

        # Create a network, three nearest nodes are supposed to be your
        # neighbours
        tree = cKDTree(coords)
        k = 4
        distances, indices = tree.query(coords, k=k)

        G = nx.Graph()

        # Add nodes
        for i, (x, y) in enumerate(coords):
            point = Point(x, y)

            get_salinity = salinity_data[salinity_data.contains(point)]
            if not get_salinity.empty:
                salinities = get_salinity.iloc[0]['Salinity']
            else:
                salinities = None
                print("Something went wrong")
            G.add_node(i, pos=(x, y), salinities=salinities)

        # Add edges
        for i, neighbors in enumerate(indices):
            for j in neighbors[1:]:  # skip the first one, that is the point itself
                G.add_edge(i, j)

        return G
