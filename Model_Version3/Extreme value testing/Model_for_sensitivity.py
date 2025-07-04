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

from Agents_for_sensitivity import Low_skilled_agri_worker, Low_skilled_nonAgri, Manual_worker, Skilled_agri_worker, Skilled_service_worker
from Agents_for_sensitivity import Other, Non_labourer, Small_land_households, Middle_land_households, Large_land_households, Landless_households
from Agents_for_sensitivity import Land_household, Working_hh_member, Migrated_household, Migrated_hh_member

# Define path
path = os.getcwd()

# Import data
correct_path = path + "\\Data\\model_input_data_824.xlsx"

# Sensitivity analysis


class RiverDeltaModel(Model):
    def __init__(
        self,
        seed=20,
        salinity_low=False,
        salinity_high=False,
        production_costs_scenario="Medium",
        wage_of_ww=1,
        wage_workers_required=1,
        district='Gò Công Đông',
        num_agents=1000,
        excel_path=correct_path,
        debt_scenario=1,
        scenario_contacts="Normal",
        chance_info_meeting=0.1,
        scenario_facilities="Normal",
        scenario_migration=1,
        salinity_shock_step=[
            25, 49, 145, 193, 241, 289]
    ):
        super().__init__(seed=seed)
        self.seed = seed
        random.seed(20)
        np.random.seed(20)

        # ATTRIBUTES FOR SENSITIVITY ANALYSIS
        self.salinity_low = salinity_low
        self.salinity_high = salinity_high
        self.production_costs_scenario = production_costs_scenario
        self.wage_of_ww = wage_of_ww
        self.wage_workers_required = wage_workers_required
        self.scenario_contacts = scenario_contacts
        self.debt_scenario = debt_scenario
        self.scenario_migration = scenario_migration
        self.scenario_facilities = scenario_facilities

        # All agents attributes are created using excel data
        self.excel_data = self.get_excel_data(excel_path)

        # Generate agents
        self.num_agents = num_agents
        self.generate_agents()

        # Define area. This is done by:
        #   - Determining the district
        #   - Load shapefile data for the districts, and load salinity data
        #   - Determine which households (=land households) need a node
        #   - Create a network
        #   - Create self.grid, using the network
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
            households_which_need_a_node,
            # HIER WAS EERST LEN(households_which_need_a_node)
            self.seed)
        self.grid = NetworkGrid(self.G)

        # Connect farmer households to the grid
        available_nodes = list(self.G.nodes())
        random.shuffle(available_nodes)

        for agent in households_which_need_a_node:
            node_id = available_nodes.pop(0)
            # DIT WAS EERDER SALINITIES
            salinity_level = self.G.nodes[node_id]["salinities"]
            agent.salinity = salinity_level
            if self.salinity_low:
                agent.salinity = 0
            elif self.salinity_high:
                agent.salinity = salinity_level * 2
            agent.node_id = node_id
            self.grid.place_agent(agent, agent.node_id)

    # Below are all the parameters, which are used in the model

        # Possibility for a salinity shock
        self.salinity_shock_step = salinity_shock_step
        self.salinity_shock = False
        self.time_since_shock = 0

        # Does the agent meet agrocensus?
        # Based on paper by Tran et al, (2020)
        self.chance_info_meeting = chance_info_meeting

        # Possibility for disease
        # Based on paper by Joffre et al., 2015 on extensive shrimp farming
        self.chance_disease = 0.16

        # Maize costs
        self.maize_fixed_costs = 3400000  # Based on paper by Ba et al., (2017)

        # Land price if someone buys your land
        self.land_price_per_ha = 78000000  # Assumption

        # possibility for migration
        self.chances_migration = [0.03, 0.01, 0.01,
                                  0.005, 0.01, 0.005]  # THESE ARE RANDOM
        self.chances_migration = [
            probability *
            self.scenario_migration for probability in self.chances_migration]
        self.chance_leaving_household = 0.005 * self.scenario_migration  # ASSUMPTION
        self.increased_chance_migration_familiarity = 0.01

        self.possible_to_change = False

        # Interest rates for loans and savings
        self.interest_rate_loans = 0.1
        self.interest_rate_savings = 0.05

        # Distribution man_days during preparation time and yield time
        self.man_days_prep = 1 / 3
        # ASSUMPTION, average / day is 200000 based on Pedroso et al., 2017
        self.payment_low_skilled = 190000 * self.wage_of_ww
        self.payment_high_skilled = 210000 * self.wage_of_ww
        self.distribution_high_low_skilled = 0

        # Number of deceased households (all household members have died)
        self.deceased_households = 0
        self.death_household_members = 0
        # Keep track of the death agents
        self.death_agents = 0
        # Number of child births
        self.child_births = 0

        # Check the total number_of_households
        self.number_of_households = 0

        for agent in self.agents:
            if agent.agent_type == "Household":
                self.number_of_households += 1

        self.start_households = self.number_of_households
        self.current_hh_left = self.number_of_households

        # number of workers and characteristics
        self.start_total_low_nonagri = len([agent for agent in self.agents if hasattr(
            agent, 'agent_occupation') and agent.agent_type == "Household_member" and agent.agent_occupation == "low_skilled_nonAgri"])

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

        # Number of work days per month
        self.work_days_per_month = 20

        # Set up datacollector
        model_metrics = model_metrics = {
            "Average_Livelihood": lambda model: mean(
                [
                    agent.livelihood['Average'] for agent in self.agents if hasattr(
                        agent,
                        'livelihood')]) if self.agents else 0,
            "Num_household_members": lambda model: sum(
                1 for agent in model.agents if getattr(
                    agent,
                    "agent_type",
                    None) == "Household_member"),
            "Migrated_households": lambda model: sum(
                1 for agent in model.agents if getattr(
                    agent,
                    "agent_type",
                    None) == "Migrated"),
            "Migrated_members": lambda model: sum(
                1 for agent in model.agents if getattr(
                    agent,
                    "agent_type",
                    None) == "Migrated_member"),
            "Migrated_individuals": lambda model: sum(
                1 for agent in model.agents if getattr(
                    agent,
                    "agent_type",
                    None) == "Migrated_member_young_adult"),
            "Died agents": lambda model: self.death_agents,
            "Child births": lambda model: self.child_births}

        agent_metrics = {
            "Crop_type": lambda a: getattr(
                a,
                "crop_type",
                None) if getattr(
                a,
                "agent_type",
                None) == "Household" else None,
            "Land_category": lambda a: getattr(
                a,
                "land_category",
                None) if getattr(
                    a,
                    "agent_type",
                    None) == "Household" else None,
            "Savings": lambda a: getattr(
                a,
                "savings",
                None) if getattr(
                a,
                "agent_type",
                None) == "Household" else None,
            "too low income": lambda a: getattr(
                a,
                "income_too_low",
                None) if hasattr(
                a,
                "income_too_low") else None,
            "Number_of_wage_workers": lambda a: getattr(
                a,
                "wage_workers",
                None) if hasattr(
                    a,
                    "wage_workers") else None}

        self.datacollector = DataCollector(
            model_reporters=model_metrics,
            agent_reporters=agent_metrics)

    def generate_agents(self):
        """
        This is the function to generate individual household member agents, and create households of them.
        The number of household members is equal to "num_agents"

        At first, the agents will get an age, and it is checked if they are working or not
        Working agents get a sector, occupation, employment type. They will be put in a class based on their occupation
        Non working agents will be in the class "Non_labourer"

        Based on sector and employment type, land households are created.
        This happens when sector != non agri, and employment type == self employed
        The land households is then filled with other household members

        If there are no individual agents left which can create a farm, landless households are created.
        Each landless household should have minimal 1 adult, and is then filled random

        """
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
                             'self_employed' and agent.agent_sector != 'Non_agri']  # These are the main farm owners, they start the farm!!

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
            self.agents.add(household)
            for member in household.household_members:
                member.household = household

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

            self.agents.add(household)
            for member in household_members:
                member.household = household

        # print number of unassigned agents
        unassigned_agents = [a for a in self.agents if hasattr(
            a, 'agent_type') and a.agent_type == "Household_member" and not a.assigned]
        print("There are", len(unassigned_agents), "agents unassigned!!")

    def step(self):
        """
        The step function of the model class determines what happens in the model.
        Each step, it is checked if a shock is happening or not.

        When self.steps % 12 == 0, it is time for the yearly activities of all agents

        Dependend on the crop, it can be time to harvest.
        Three times a year, the non agri workers get paid

        After payment, the households will check whether their income is sufficient or not
        Then there is a possibility to change crops or e.g. migrate

        Once a year, the data is collected
        """
        self.agents.shuffle_do('step')

        self.number_of_households = 0

        for agent in self.agents:
            if hasattr(agent, "time_since_last_savings_check"):
                agent.time_since_last_savings_check += 1
            if agent.agent_type == "Household":
                self.number_of_households += 1

        self.current_hh_left = self.number_of_households / self.start_households

        # Check if a shock is happening
        self.check_shock()

        # It is only possible to change when 12 steps are done
        if self.steps > 13:
            self.possible_to_change = True
        for agent in self.agents:
            if hasattr(agent, "waiting_time_"):
                for key in agent.waiting_time_:
                    if agent.waiting_time_[key] > 0:
                        agent.waiting_time_[key] -= 1

        self.pay_other_agents()

        if self.steps % 12 == 0:
            self.agents.do(
                lambda agent: agent.yearly_activities() if isinstance(
                    agent,
                    (Working_hh_member,
                     Land_household,
                     Landless_households,
                     Non_labourer)) else None)
            self.need_to_yield(["Coconut"])
            self.agents.do(
                lambda agent: agent.update_experience() if isinstance(
                    agent, Land_household) else None)
            self.pay_wage_workers()
            # self.pay_other_agents()
            self.farmers_check_situation()
            self.reset_wage_worker_payment()
            # Reset yearly income
            self.reset_yearly_income()

        month = self.steps % 12

        # In february we harvest rice and coconut
        if month == 2:
            self.need_to_yield(["Rice", "Coconut"])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.reset_wage_worker_payment()

        # In April we harvest coconut, Maize and shrimp
        elif month == 4:
            self.need_to_yield(["Coconut", "Maize", "Shrimp"])
            self.pay_wage_workers()
            # self.pay_other_agents()
            self.farmers_check_situation()
            self.reset_wage_worker_payment()

        # In June we harvest coconut
        elif month == 6:
            self.need_to_yield(['Coconut'])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.reset_wage_worker_payment()

        # In August we harvest Rice, Maize and coconut
        elif month == 8:
            self.need_to_yield(["Rice", "Maize", 'Coconut'])
            self.pay_wage_workers()
            # self.pay_other_agents()
            self.farmers_check_situation()
            self.reset_wage_worker_payment()

        # In October we harvest shrimp and coconut
        elif month == 10:
            self.need_to_yield(["Shrimp", 'Coconut'])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.reset_wage_worker_payment()

        # In November we harvest rice
        elif month == 11:
            self.need_to_yield(["Rice"])
            self.pay_wage_workers()
            self.farmers_check_situation()
            self.reset_wage_worker_payment()

        # Once a year, the data is collected
        if self.steps % 12 == 0:
            # Collect data
            self.datacollector.collect(self)
        # self.datacollector.collect(self)

    def need_to_yield(self, crop_type):
        """
        Function which determines which farmers need to harvest a certain crop.
        When they have done that, they need to pay the wage workers
        """

        for crop in crop_type:
            for agent in list(self.agents):
                if isinstance(agent, Land_household):
                    if crop in agent.crops_and_land.keys() and agent.waiting_time_[
                            crop] == 0:
                        agent.harvest(crop)
                        agent.wage_worker_payment = 1

    def pay_wage_workers(self):
        """
        All farmers who harvest, need to pay their wage workers.
        This functions select those workers, calculates their income and increases the income of the individual workers
        """
        # select all wage workers
        selected_agents = [
            agent for agent in self.agents if agent.agent_type == "Household_member" and getattr(
                agent, 'agent_employment_type', None) == "employee" and hasattr(
                agent, 'agent_sector') and agent.agent_sector != "Non_agri"]
        # Calculate number of low skilled wage workers
        sum_low_skilled = sum(1 for agent in selected_agents if getattr(
            agent, 'agent_occupation', None) == "low_skilled_agri_worker")
        # Calculate number of high skilled wage workers
        sum_high_skilled = sum(1 for agent in selected_agents if getattr(
            agent, 'agent_occupation', None) == "skilled_agri_worker")
        if sum_low_skilled == 0 and sum_high_skilled == 0:
            print("niemand wil op de farm werken")
            self.distribution_high_low_skilled = 0
        else:
            # Calculate distribution of high and low skilled wage workers
            self.distribution_high_low_skilled = sum_low_skilled / \
                (sum_low_skilled + sum_high_skilled)

        # Check total days wage workers were needed, to define number of work
        # days for the wage workers
        total_days_ww_used = sum(
            agent.household_size for agent in self.agents if isinstance(
                agent, Land_household) and agent.wage_worker_payment == 1)
        total_ww = sum_low_skilled + sum_high_skilled

        # Determine the work days per wage worker
        work_days_per_ww = total_days_ww_used / total_ww
        # Pay the wage workers
        for agent in selected_agents:
            if agent.agent_occupation == "low_skilled_agri_worker":
                agent.income += self.payment_low_skilled * work_days_per_ww
            elif agent.agent_occupation == "skilled_agri_worker":
                agent.income += self.payment_high_skilled * work_days_per_ww

    def farmers_check_situation(self):
        """
        Function for all farmers who have just harvested.
        The land households update their savings
        """
        # alle farm household agents die nu yield hebben gehad checken hun
        # savings en kijken of iets moet veranderen!!
        for agent in list(self.agents):
            if isinstance(agent, Land_household):
                if agent.wage_worker_payment == 1:
                    agent.check_savings()

    def reset_wage_worker_payment(self):
        for agent in list(self.agents):
            if isinstance(agent, Land_household):
                agent.wage_worker_payment = 0

    def reset_yearly_income(self):
        # At the end of the year, all incomes are set to zero
        for agent in list(self.agents):
            if hasattr(agent, "yearly_income"):
                agent.yearly_income = 0

    def pay_other_agents(self):
        """Three times per year, it is time to pay the non agri household members

        For each occupation, the ratio of workers left in the occupation is calculated.
            As a result, when a lot of workers are leaving, you will receive more income

        Except for service workers, their income can also decrease
            This happens when a lot of people are migrating
        """
        # Pay Low skilled non agri workers and other workers
        selected_agents = [
            agent for agent in self.agents if hasattr(
                agent,
                'agent_occupation') and agent.agent_type == "Household_member" and agent.agent_occupation == "low_skilled_nonAgri"]
        total_low_skilled_nonagri = len(selected_agents)
        for agent in selected_agents:
            income_increase = self.start_total_low_nonagri / total_low_skilled_nonagri
            agent.income += income_increase * self.payment_low_skilled * \
                self.work_days_per_month

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
            agent.income += income_increase * income * self.work_days_per_month

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
                self.payment_high_skilled * self.work_days_per_month

        # Agents need to update their income and see if it is sufficient
        if self.steps % 12 == 4:
            for agent in list(self.agents):
                if hasattr(agent, 'check_income'):
                    agent.check_income(4)

    def check_shock(self):
        """
        Function to check each step if a salinity shock has happened
        In addition, the salinity experience increases of the agents
        If a shock did happen last step, the salinity should be decreased again
        """
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
        """
        Function to give the land households a land category
        This is based on the probabilities of the excel file
        Land categories can be small, medium and large
        """
        chance_land_size = self.random.random()
        for key, (low, high) in land_sizes.items():
            if low <= chance_land_size <= high:
                return key

    def get_land_area(self, land_category):
        """
        Based on the land area, the land households have a land size
        Small land size will be between 0 and 0.5 ha
        Medium land size between 0.5 - 2 ha
        Large land size is bigger than 2 ha
        """
        if land_category == "small":
            return self.random.uniform(0.3, 0.5)
        elif land_category == "medium":
            return self.random.uniform(0.5, 2)
        elif land_category == "large":
            return self.random.uniform(2, 5)
        return 0

    def get_unassigned_by_age_group(self, unassigned_agents):
        """
        When landless households are created, minimal 1 adult household member is required.
        This function checks how many children, adults, and elderly are unassigned
        """
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
        """
        All household agents have a housing quality.
        This is based on excel data, using a mean and std dev
        """
        mean = self.excel_data['housing_quality']['mean']
        std = self.excel_data['housing_quality']['std_dev']
        return min(1.0, max(0.0, self.random.normalvariate(mean, std)))

    def number_of_members_per_type(self, number):
        """
        When creating land households, the household needs to be filled with
            self agri workers, self wage workers and self non agri workers

        This function takes the average number of household members in this category per land size,
            and makes this an int.
        (it is not possible to have 1.9 farm workers on your farm, it should be 1 or 2)
        """
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
        """
        When the number of self agri, self non agri and wage workers in the household is determined,
            These are added to the household using this function
        """
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

        # The agents are shuffled, and a random agent is chosen
        self.random.shuffle(possible_agents)
        for a in possible_agents[:count]:
            a.assigned = True
            household.append(a)

    def get_age(self, age_distribution):
        """
        Function to check the age of household member during the creation of the agent
        """
        chance_age = self.random.random()
        cumulative = 0
        for (low, high), probability in age_distribution.items():
            cumulative += probability
            if chance_age <= cumulative:
                age = self.random.randint(low, high)
                return age

    def is_working(self, age, work_per_agegroup):
        """
        Function to check if a household member is working or not during the creation of the agent
        """
        for (low, high), chance in work_per_agegroup.items():
            if low <= age <= high:
                return self.random.random() < chance
        return False

    def define_sector(self, sector_distribution):
        """
        Function to check the sector of a working household member, during the creation of the agent
        """
        chance_sector = self.random.random()
        for sector, (low, high) in sector_distribution.items():
            if low <= chance_sector <= high:
                agent_sector = sector
                return agent_sector

    def define_occupation(self, agent_sector, occupation_distribution):
        """
        Function to check the occupation of a working household member, during the creation of the agent
        """
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
        """
        Function to check the employment type of a working household member, during the creation of the agent
        This is based on the agent sector and agent occupation, using the excel file.
        """
        employment_types = employment_distribution[agent_sector][agent_occupation]['employment_distribution']
        chance_employment = self.random.random()
        cumulative = 0
        for employment_type, probability in employment_types.items():
            cumulative += probability
            if chance_employment <= cumulative:
                agent_employment = employment_type
                return agent_employment

    def get_excel_data(self, excel_path):
        """
        This function is used to read all the excel sheets, and add all the data in a dictionary.

        What happens is that for each factor, e.g. age distribution,
            the data is read using the function "self.process_age_distribution".

            Those functions process the data, and put it in the items of the dictionary.
            When using this get_excel_data function with the correct key,
            access to the correct data is provided.
        """
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
        """
        Function to read the excel data for age distributions,
        and create a dictionary for in the get_excel_function
        """
        age_dist = {}
        for i, row in df.iterrows():
            low, high = map(int, row['age_group'].split('-'))
            age_dist[(low, high)] = row['percentage']
        return age_dist

    def process_work_per_agegroup(self, df):
        """
        Function to read the excel data if an individual is working or not,
        this is based on their age group, and put in a dictionary.
        This dictionary can be accessed using the get_excel data function
        """
        work_dict = {}
        for i, row in df.iterrows():
            low, high = map(int, row['age_group'].split('-'))
            work_dict[(low, high)] = row['working'] / 100
        return work_dict

    def process_sector_distribution(self, df):
        """
        Function to read the excel data for different sector types and probabilities,
        and create a dictionary for in the get_excel_function
        """
        sector_dict = {}
        cumulative = 0
        for i, row in df.iterrows():
            prob = row['Probability']
            sector = row['Sector']
            sector_dict[sector] = (cumulative, cumulative + prob)
            cumulative += prob
        return sector_dict

    def process_occupation_employment_distribution(self, df):
        """
        Function to read the excel data for occupations and employment.
        This excel sheet shows the sector, occupations with percentages,
            and employment types with percentages.

        The sectors, occupations and employment types are put together in a nested dictionary
        """
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
        """
        Function to read the excel data to see the mean and std dev of household sizes,
        and create a dictionary for in the get_excel_function with the mean and std dev
        """
        mean = float(df[df.iloc[:, 0] == 'mean'].iloc[0, 1])
        std_dev = float(df[df.iloc[:, 0] == 'std_dev'].iloc[0, 1])
        return {'mean': mean, 'std_dev': std_dev}

    def process_land_sizes(self, df):
        """
        Function to read the excel data for the distribution of land sizes,
        and create a dictionary with land categories and probabilities for in the get_excel_function
        """
        size_probabilities = {}
        cumulative = 0
        for i, row in df.iterrows():
            cat = row['land_size_type']
            prob = row['percentage']
            size_probabilities[cat] = (cumulative, cumulative + prob)
            cumulative += prob
        return size_probabilities

    def process_work_type_per_land_size(self, df):
        """
        Function to read the excel data for work types per land size

        In the excel sheet, there is per dominant income source and land size,
            a probiability someone works in self agri, self non agri and wage
            in the family.
        These probabilities are placed in a nested dictionary for in the get_excel_function
        """
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
        """
        Function to read the excel data for house quality,
        and create a dictionary with the mean and std dev for in the get_excel_function
        """
        df = df.set_index('hh_quality')
        return {'mean': df.loc['mean', 'value'],
                'std_dev': df.loc['std_dev', 'value']}

    def process_population_statistics(self, df):
        """
        Function to read the excel data for statistics such as birth rate,
            mean death age and std dev death age.
        These statistics are put in a dictionary for in the get_excel_function
        """
        statistics_population = dict(zip(df["Statistic"], df["Value"]))
        return statistics_population

    def process_education_levels(self, df):
        """
        Function to read the excel data for education level per age group,
        and create a nested dictionary for in the get_excel_function
        """
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
        """
        Function to read the excel data for experience and machines,
            the probabilities are per occupation
        A nested dictionary is created for in the get_excel_function.
        """
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
        """
        Function to read the excel data for dissabilities per age group

        There is a nested dictionary, per age and functioning with how much,
            difficulty someone could have in percentages.

        Example: {{59-85:{"Hearing":{"No_difficulty":0.87, "Unable": 0.05,... }}}}

        This dictionary can be loaded using the get_excel_function
        """
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
        """
        Function to read the excel data to check if households are member of an association
        and return a percentage for in the get_excel_function
        """
        for i, row in df.iterrows():
            if row['Association'] == "yes":
                percentage_association = row['Percentage']
        return percentage_association

    def gather_shapefiles(self, district):
        """
        This function is used to open the district-salinity gpkg file,
            and the district boundaries gpkg file.

        These two datasets are then stored in self.data_salinity, self.polygon_districts,
        to have easy and fast acces to them.
        """
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

        # Select the correct district
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
        """
        Function to create a network for the land household agents, and place the agents on the map based on their salinity level
        """

        districts_polygon.set_crs(salinity_data.crs, inplace=True)
        # Generate enough points to make sure there is always a match for the
        # agents
        candidate_points = districts_polygon.sample_points(
            size=len(land_agents) * 50, seed=seed)
        point_geoms = list(candidate_points.geometry[0].geoms)

        # Determine salinity per point
        point_data = []
        for pt in point_geoms:
            salinity_match = salinity_data[salinity_data.contains(pt)]
            if not salinity_match.empty:
                salinity = salinity_match.iloc[0]['Salinity']
                point_data.append((pt, salinity))

        # Look at low and high salinity points, to match the agent crops with the points
        # Maize and rice farmers require low salinity, coconut and shrimp can
        # also function with high salinity levels
        low_salinity_points = [(pt, sal) for pt, sal in point_data if sal < 4]
        high_salinity_points = [(pt, sal)
                                for pt, sal in point_data if sal >= 4]

        coords = []
        salinities = []

        crop_type_to_salinity = {
            "Rice": "low",
            "Annual crops": "low",
            "Perennial crops": "high",
            "Aquaculture": "high"
        }

        # Give the agents a salinity level
        for agent in land_agents:
            crop_type = agent.crop_type
            sal_pref = crop_type_to_salinity.get(crop_type, "low")

            if sal_pref == "low" and low_salinity_points:
                pt, sal = low_salinity_points.pop(
                    np.random.randint(len(low_salinity_points)))
            elif sal_pref == "high" and high_salinity_points:
                pt, sal = high_salinity_points.pop(
                    np.random.randint(len(high_salinity_points)))
            else:
                # Give a warning when there are no points available
                pt, sal = point_data.pop(np.random.randint(len(point_data)))
                print(f"Fallback is used for {crop_type}")

            coords.append((pt.x, pt.y))
            salinities.append(sal)

        coords = np.array(coords)

        # Create network
        tree = cKDTree(coords)
        k = 4
        distances, indices = tree.query(coords, k=k)

        G = nx.Graph()
        for i, (x, y) in enumerate(coords):
            G.add_node(
                i,
                pos=(
                    x,
                    y),
                salinities=salinities[i],
                crop_type=land_agents[i].crop_type)

        for i, neighbors in enumerate(indices):
            for j in neighbors[1:]:
                G.add_edge(i, j)

        return G
