from mesa import Agent, Model

import numpy as np
import random
from Functions2 import create_household, die, child_birth, education_levels, salinity_influence_neighbours, calculate_livelihood_agrifarm, advice_agrocensus, advice_neighbours, define_abilities, define_motivations
from Functions2 import calculate_MOTA,  best_MOTA, change_crops, calculate_cost, calculate_yield_agri, calculate_income_farming, calculate_farmers_spend_on_ww
class Agri_farmer(Agent):
    def __init__(self, model, agent_type, node_id):
        super().__init__(model)
        self.agent_type = agent_type
        self.node_id = node_id

        # Define households
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.education_level = education_levels(self)
        self.facilities_in_neighbourhood = 1

        # Define income
        self.government_support = 0
        self.meeting_agrocensus = 0
        self.cost_farming = 0
        self.yield_ = 0
        self.income = 0
        
        
    def step(self):
       pass

    def yearly_activities(self):
        # Each agent is one year older
        self.ages = [age + 1 for age in self.ages]
        # Possibility for an agent to die
        self.ages = die(self.ages)
        # Possiblity a child is born
        self.ages = child_birth(self.ages, birth_rate = 0.2, maximum_number_of_children = 5) 

        # Change salinity levels based on neighbours
        self.salinity = salinity_influence_neighbours(self.model, self.node_id)

        
        # Did you visit a governmental meeting?
        self.meeting_agrocensus = 1 if np.random.rand() > 0.1 else 0 # Based on paper Tran et al., (2020)
        # Calculate livelihood
        self.livelihood = calculate_livelihood_agrifarm(self.meeting_agrocensus, self.education_level, self.salt_experience, 
        self.government_support, self.savings, self.loan_size, self.maximum_debt, self.land_size, self.salinity)

        # Decide on next crop
        self.possible_next_crops = [self.current_crop] # It is always possible to change nothing and have the same crop as the previous year
        # Check if there is advice from agrocensus meeting you attended
        if self.meeting_agrocensus == 1:
            self.possible_next_crops = advice_agrocensus(self.salinity)
        # Check what your neighbours are doing
        self.possible_next_crops = advice_neighbours(self.possible_next_crops, self.model, self.node_id)
        # Check your abilities per possible crop:
        self.abilities = define_abilities(self.possible_next_crops, self.savings, self.loan_size, self.maximum_debt, self.livelihood['human'], self.salinity, self.water_level)
        # Check your motivations per possible crop:
        self.motivations = define_motivations(self.possible_next_crops, self.income, self.abilities)
        # Calculate MOTA scores and find the best crop:
        self.MOTA_scores = calculate_MOTA(self.motivations, self.abilities)
        self.new_crop = best_MOTA(self.MOTA_scores, self.current_crop)
        if self.new_crop != self.current_crop:
            # Change savings based on crop choice
            self.savings, self.loan_size, self.maximum_debt = change_crops(self.new_crop, self.savings, self.loan_size, self.maximum_debt)

        # Need to pay for the wage workers:
        self.income_spent_on_ww = calculate_farmers_spend_on_ww(self.income, self.number_of_ww, self.household_size)
        self.savings += self.income - self.cost_farming - self.income_spent_on_ww

    def reset_income(self):
        self.income = 0
        self.yield_ = 0
        self.cost_farming = 0


    def harvest(self):
        # Calculate costs based on land size
        self.cost_farming += calculate_cost(self.current_crop, self.land_size)

        # Calculate total yield in ton
        self.yield_ += calculate_yield_agri(self.current_crop, self.salinity, self.land_size)

        # Calculate income based on yield and costs, and update savings
        self.income += calculate_income_farming(self.current_crop, self.yield_)
        

        self.current_crop = self.new_crop

        

class Agri_small_saline(Agri_farmer):
    def __init__(self, model, agent_type, node_id):
        super().__init__(model, "Agri_small_saline", node_id)  
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)

        # Farm related
        self.salinity = np.random.normal(4, 1)
        self.salt_experience = 1
        self.land_size = np.random.normal(1.9, 1)
        self.current_crop = random.choice(["Rice"])
        self.new_crop = self.current_crop
        self.water_level = 6
        self.number_of_ww = random.choice([0,1,2])

        # Financial
        self.savings = np.random.normal(4000, 1000)
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300) # Define later
        self.value_of_assets = self.land_size * 3000 + self.house_price # Define later
        self.maximum_debt = self.value_of_assets

    def step(self):
        pass

class Agri_small_fresh(Agri_farmer):
    def __init__(self, model, agent_type, node_id):
        super().__init__(model, "Agri_small_fresh", node_id)
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)

        # Farm related
        self.salinity = np.random.normal(2, 0.5)
        self.salt_experience = 0
        self.land_size = np.random.normal(1.9, 1)
        self.current_crop = "Rice"
        self.new_crop = self.current_crop
        self.water_level = 8
        self.number_of_ww = random.choice([0,1,2])

        # Financial
        self.savings = np.random.normal(4000, 1000)
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300) # Define later
        self.value_of_assets = self.land_size * 3000 + self.house_price # Define later
        self.maximum_debt = self.value_of_assets

    def step(self):
        pass

class Low_skilled_wage_worker(Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)

        self.agent_type = agent_type
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)

        self.income = 100
        self.minimum_income = self.household_size * 1100 # ASSUMPTION how much life costs per household member per year
        self.working_force = 0

    def step(self):
        pass

    def yearly_activities(self):
        self.working_force = [num for num in self.ages if 15 <= num <= 59]

        


