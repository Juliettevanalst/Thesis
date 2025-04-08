from mesa import Agent, Model

import numpy as np
import random
from Functions2 import create_household, die, child_birth, education_levels, calculate_livelihood_agrifarm, advice_agrocensus, advice_neighbours, define_abilities, define_motivations
from Functions2 import calculate_MOTA,  best_MOTA, change_crops, calculate_cost, calculate_yield_agri, calculate_income_farming, calculate_farmers_spend_on_ww, calculate_migration_ww, decide_change_ww
class Agri_farmer(Agent):
    def __init__(self, model, agent_type, node_id, salinity):
        super().__init__(model)
        self.agent_type = agent_type
        self.node_id = node_id
        self.salinity = salinity

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
        #self.salinity = salinity_influence_neighbours(self.model, self.node_id) apparently this does not happen

        
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
    def __init__(self, model, agent_type, node_id, salinity):
        super().__init__(model, "Agri_small_saline", node_id, salinity)  
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)

        # Farm related
        #self.salinity = np.random.normal(4, 1)
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
    def __init__(self, model, agent_type, node_id, salinity):
        super().__init__(model, "Agri_small_fresh", node_id, salinity)
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)

        # Farm related
        #self.salinity = np.random.normal(2, 0.5)
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
        self.child_who_can_work = 0

        self.contacts_in_city = 1
        self.saw_advertisement = 1
        self.change_children = None
        self.change_leaving_household = 0.1
        self.facilities_in_neighbourhood = 1

    def step(self):
        pass

    def yearly_activities(self):
         # Each agent is one year older
        self.ages = [age + 1 for age in self.ages]
        # Possibility for an agent to die
        self.ages = die(self.ages)
        # Possiblity a child is born
        self.ages = child_birth(self.ages, birth_rate = 0.2, maximum_number_of_children = 5) 
        # Define working force
        self.working_force = len([num for num in self.ages if 15 <= num <= 59]) + self.child_who_can_work

    def receive_income(self):
        # We need to change as household since the income is too low?
        if self.income < self.minimum_income:
            self.income_too_low = 1
            self.possible_changes = ["migration", "increase_working_force", "switch to aqua/agri"]
        self.chance_migration = calculate_migration_ww(self.income_too_low, self.contacts_in_city,  self.facilities_in_neighbourhood)
        if np.random.rand() < self.chance_migration:
            pass #print("agent becomes migrated agent")
            # AGENT WORDT EEN MIGRATED AGENT
        else:
            self.change, self.agent_type, self.working_force, self.child_who_can_work = decide_change_ww(self.model.income_per_agri_ww, self.model.income_per_aqua_ww, self.income, self.working_force, self.agent_type, self.ages)

        # What do the young adults/parents want?
        num_children = len([num for num in self.ages if 15 <= num <= 35])
        if np.random.rand() < self.model.chance_leaving_household: # They want to leave
            self.children_possibilities = ["migration", "work_in_factory"]
            if self.saw_advertisement == 1 and self.contacts_in_city == 1:
                self.change_children = "migration"
            elif self.model.factory_in_neighborhood == True:
                self.change_children = "work_in_factory"

            if self.change_children == "migration":
                migrated_agent_ages  = len([l for l in self.ages if (15 <= l <= 35)])
                self.ages = [l for l in self.ages if not (15 <= l <= 35)] # Delete them from the list of ages
                for i in range(migrated_agent_ages):
                    migrated = Migrated(self)
                    print("agent migrates")
                    self.model.agents.add(migrated)

            if self.change_children == "work_in_factory":
                self.ages = [l for l in self.ages if not (15 <= l <= 35)]
                # HIER MOET KMEN DAT JE DAN EEN FACTORY WAGE WORKER BENT

class Migrated(Agent):
    def __init__(self, model):
        super().__init__(model)

        self.ages = 0

    def step(self):
        pass


                







