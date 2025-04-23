from mesa import Agent, Model

import numpy as np
import random
from Functions2 import create_household, die, child_birth, education_levels, calculate_livelihood_agrifarm, advice_agrocensus, advice_neighbours, define_abilities, define_motivations
from Functions2 import calculate_MOTA,  best_MOTA, change_crops, calculate_cost, calculate_yield_agri, calculate_income_farming, calculate_farmers_spend_on_ww, calculate_migration_ww, decide_change_ww
from Functions2 import calculate_cost_aqua, calculate_income_aqua, calculate_yield_aqua, calculate_migration_chance_agri, transfer_land, annual_loan_payment

# Agri farmers
class Agri_farmer(Agent):
    def __init__(self, model, agent_type, node_id, salinity):
        super().__init__(model)
        self.agent_type = agent_type
        self.node_id = node_id
        self.salinity = salinity

        # Define households
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.living_costs = self.household_size * 1000 # ASSUMPTION, EACH HOUSEHOLD MEMBERS LIVING COSTS ARE 1100 EUROS PER YEAR
        self.loan_size = 0
        self.pay_loan = 0
        self.required_income = self.living_costs + 0.2 * self.loan_size
        self.education_level = education_levels(self)
        self.facilities_in_neighbourhood = 1
        self.contacts_in_city = 0

        # Define income
        self.government_support = 0
        self.meeting_agrocensus = 0
        self.cost_farming = 0
        self.yield_ = 0
        self.income = 0
        self.yield_time_crops = {"Rice":6, "Mango":12, "Coconut": 12, "Shrimp":8}

        # Related to crops
        self.growth_time = 0
        self.salinity_during_shock = 0
        
        
    def step(self):
       pass

    def yearly_activities(self):
        # Each agent is one year older
        self.ages = [age + 1 for age in self.ages]
        # Possibility for an agent to die
        self.ages = die(self.ages)
        # Possiblity a child is born
        self.ages = child_birth(self.ages, birth_rate = 0.2, maximum_number_of_children = 5) 

        # update savings
        self.savings += self.income - self.cost_farming - self.living_costs - self.pay_loan
        self.loan_size - self.pay_loan
        self.savings = self.savings * (self.model.interest_rate_savings + 1)
        
        # Did you visit a governmental meeting?
        self.meeting_agrocensus = 1 if np.random.rand() > 0.1 else 0 # Based on paper Tran et al., (2020)

        # Do you have contacts in the city?
        if random.random() < self.model.migration_ratio and self.contacts_in_city == 0:
            self.contacts_in_city = 1

        # Calculate livelihood
        self.livelihood = calculate_livelihood_agrifarm(self.meeting_agrocensus, self.education_level, self.salt_experience, 
        self.government_support, self.savings, self.loan_size, self.maximum_debt, self.land_size, self.salinity)

        # Check if the agent will migrate or not
        self.chance_migration = calculate_migration_chance_agri(self.livelihood)
        self.chance_migration
        if random.random() < self.chance_migration:
            # neighbor with the highest livelihood will get your land. However, this is possible after the first year, since otherwise not all agents do have a livelihood defined
            if self.model.steps > 12:
                transfer_land(self.land_size, self.node_id, self.model)
            for i in range(len(self.ages)):
                migrated = Migrated(self.model, agent_type = "migrated")
                self.model.agents.add(migrated)
            self.model.agents.remove(self) 

        # Decide on next crop
        self.possible_next_crops = [self.current_crop] # It is always possible to change nothing and have the same crop as the previous year
        # Check if there is advice from agrocensus meeting you attended
        if self.meeting_agrocensus == 1:
            self.possible_next_crops = advice_agrocensus(self.salinity)
        # Check what your neighbours are doing
        self.possible_next_crops = advice_neighbours(self.possible_next_crops, self.model, self.node_id)
        # Check your abilities per possible crop:
        self.abilities = define_abilities(self.possible_next_crops, self.savings, self.loan_size, self.maximum_debt, self.livelihood['human'], self.salinity, self.current_crop)
        # Check your motivations per possible crop:
        self.motivations = define_motivations(self.possible_next_crops, self.income, self.abilities, self.current_crop, self.required_income)
        # Calculate MOTA scores and find the best crop:
        self.MOTA_scores = calculate_MOTA(self.motivations, self.abilities)
        self.new_crop = best_MOTA(self.MOTA_scores, self.current_crop)
        if self.new_crop != self.current_crop:
            # Change savings based on crop choice
            self.savings, self.loan_size, self.maximum_debt = change_crops(self.new_crop, self.savings, self.loan_size, self.maximum_debt)
            # Calculate how much you need to pay each year to pay back your loan in 5 years
            self.pay_loan = annual_loan_payment (self.loan_size, self.model.interest_rate_loans)

        # Need to pay for the wage workers:
        self.income_spent_on_ww = calculate_farmers_spend_on_ww(self.income, self.number_of_ww, self.household_size)
        self.savings -= self.income_spent_on_ww

    def reset_income(self):
        self.income = 0
        self.yield_ = 0
        self.cost_farming = 0


    def harvest(self):
        # if a shock happened during growth time, we need to take that salinity into account, otherwise, current salinity
        if self.model.time_since_shock > self.growth_time:
            self.salinity_during_shock = self.salinity

        # Calculate costs based on land size
        self.cost_farming += calculate_cost(self.current_crop, self.land_size)

        # Calculate total yield in ton
        self.yield_ += calculate_yield_agri(self.current_crop, self.salinity_during_shock, self.land_size)

        # Calculate income based on yield and costs, and update savings
        self.income += calculate_income_farming(self.current_crop, self.yield_)
        

        self.current_crop = self.new_crop
        self.growth_time = 0
        self.yield_time = self.yield_time_crops[self.current_crop]

        

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
        self.number_of_ww = random.choice([0,1,2])
        self.yield_time = self.yield_time_crops[self.current_crop]

       

        # Financial
        self.savings = np.random.normal(4000, 1000)
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
        self.salt_experience = 0
        self.land_size = np.random.normal(1.9, 1)
        self.current_crop = "Rice"
        self.new_crop = self.current_crop
        self.number_of_ww = random.choice([0,1,2])
        self.yield_time = self.yield_time_crops[self.current_crop]


        # Financial
        self.savings = np.random.normal(4000, 1000)
        self.house_price = np.random.normal(2000, 300) # Define later
        self.value_of_assets = self.land_size * 3000 + self.house_price # Define later
        self.maximum_debt = self.value_of_assets

    def step(self):
        pass

# Aqua farmers
class Aqua_farmer(Agent):
    def __init__(self, model, agent_type, node_id, salinity):
        super().__init__(model)
        self.agent_type = agent_type
        self.node_id = node_id
        self.salinity = salinity

        # Define households
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.living_costs = self.household_size * 1000 # ASSUMPTION, EACH HOUSEHOLD MEMBERS LIVING COSTS ARE 1100 EUROS PER YEAR
        self.loan_size = 0
        self.required_income = self.living_costs + 0.2 * self.loan_size
        self.education_level = education_levels(self)
        self.facilities_in_neighbourhood = 1
        self.contacts_in_city = 0

        # Define income
        self.government_support = 0
        self.meeting_agrocensus = 0
        self.cost_farming = 0
        self.yield_ = 0
        self.income = 0
        self.yield_time_crops = {"Shrimp":8}
        self.farm_type = random.choice(["Extensive"]) # Later add intensive and integrated mangrove shrimp

        # Related to fish
        self.growth_time = 0
        self.salinity_during_shock = 0
        self.yield_time = 2
        self.disease = 0

    def step(self):
        pass

    def yearly_activities(self):
        # Each agent is one year older
        self.ages = [age + 1 for age in self.ages]
        # Possibility for an agent to die
        self.ages = die(self.ages)
        # Possiblity a child is born
        self.ages = child_birth(self.ages, birth_rate = 0.2, maximum_number_of_children = 5) 

        # update savings
        self.savings += self.income - self.cost_farming - self.living_costs
        self.savings = self.savings * (self.model.interest_rate_savings + 1) # Receive interest 

        # Do you have contacts in the city?
        if random.random() < self.model.migration_ratio and self.contacts_in_city == 0:
            self.contacts_in_city = 1
        
        # Did you visit a governmental meeting?
        self.meeting_agrocensus = 1 if np.random.rand() > 0.1 else 0 # Based on paper Tran et al., (2020)

        # Determine farming time the farmer has left
        if self.use_antibiotics == 1:
            self.farming_time_left -= 1
        
        # If a farm has 0 time left, they will migrate to the city ASSUMPTION
        if self.farming_time_left <= 0:
            print("This farm failed due to antibiotic use")
            if self.model.steps > 12:
                transfer_land(self.land_size, self.node_id, self.model)
            for i in range(len(self.ages)):
                migrated = Migrated(self.model, agent_type = "migrated")
                self.model.agents.add(migrated)
            self.model.agents.remove(self) 

        # Calculate livelihood
        self.livelihood = calculate_livelihood_agrifarm(self.meeting_agrocensus, self.education_level, self.salt_experience, 
        self.government_support, self.savings, self.loan_size, self.maximum_debt, self.land_size, self.salinity)

    def reset_income(self): # At the end of each year, we should reset the income for the next year. However, this should happen after the datacollector collected the data, therefore there is a new function for this. 
        self.income = 0
        self.yield_ = 0
        self.cost_farming = 0

    def harvest(self):
        # Did you get a disease this season?
        self.disease = 1 if np.random.rand() <= self.model.chance_disease[self.farm_type] else 0

        # Do you want to use antibiotics? DEZE KOSTEN GELD!! 
        if self.disease == 1:
            if np.random.rand() <= self.model.use_antibiotics[self.agent_type]:
                self.use_antibiotics = 1
            else:
                self.use_antibiotics = 0

        # Calculate costs based on land size
        self.cost_farming += calculate_cost_aqua(self.current_crop, self.farm_type, self.land_size, self.disease)

        # Calculate yield
        self.yield_ = calculate_yield_aqua(self.land_size, self.current_crop, self.disease, self.farm_type)

        # Calculate income based on yield 
        self.income += calculate_income_aqua(self.current_crop, self.yield_)        

        # Reset growth time, and determine time it takes to grow the next crop
        self.growth_time = 0
        self.yield_time = self.yield_time_crops[self.current_crop]


class Aqua_small_saline(Aqua_farmer):
    def __init__(self, model, agent_type, node_id, salinity):
        super().__init__(model, "Aqua_small_saline", node_id, salinity)  
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)

        self.salt_experience = 0
        self.land_size = np.random.normal(1.9, 1)
        self.current_crop = "Shrimp"
        self.number_of_ww = random.choice([0,1,2])
        self.farming_time = np.random.randint(0,10) # How long are we already farming?
        self.farming_time_left = 10 # You can farm for 10 years on antibiotics, if you used antibiotics, your farming time will decrease by 1 each year. Otherwise, this will stay the same
        self.use_antibiotics = 0

        # Financial
        self.savings = np.random.normal(4000, 1000)
        self.house_price = np.random.normal(2000, 300) # Define later
        self.value_of_assets = self.land_size * 3000 + self.house_price # Define later
        self.maximum_debt = self.value_of_assets


    def step(self):
        pass

# Low skilled wage workers
class Low_skilled_wage_worker(Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)

        self.agent_type = agent_type
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.living_costs = 1100 * self.household_size # ASSUMPTION

        # Related to working
        self.income = 100
        self.minimum_income = self.household_size * 1100 # ASSUMPTION how much life costs per household member per year
        self.working_force = len([num for num in self.ages if 15 <= num <= 59])
        self.child_who_can_work = 0

        # Related to migrating
        self.contacts_in_city = 0
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

        # Do you have contacts in the city?
        if random.random() < self.model.migration_ratio and self.contacts_in_city == 0:
            self.contacts_in_city = 1

    def receive_income(self):
        # We need to change as household since the income is too low?
        if self.income < self.minimum_income:
            self.income_too_low = 1
            self.possible_changes = ["migration", "increase_working_force", "switch to aqua/agri"]
        else:
            self.income_too_low = 0
        self.chance_migration = calculate_migration_ww(self.income_too_low, self.contacts_in_city,  self.facilities_in_neighbourhood)
        if np.random.rand() < self.chance_migration:
            for i in range(len(self.ages)):
                migrated = Migrated(self.model, agent_type = "migrated")
                self.model.agents.add(migrated)
            self.model.agents.remove(self) # Delete the household as 
            
        else:
            self.change, self.agent_type, self.working_force, self.child_who_can_work = decide_change_ww(self.model.income_per_agri_ww, self.model.income_per_aqua_ww, self.income, self.working_force, self.agent_type, self.ages)

        # What do the young adults/parents want?
        num_children = len([num for num in self.ages if 15 <= num <= 35])
        if np.random.rand() < self.model.chance_leaving_household: # They want to leave
            self.children_possibilities = ["migration"]
            if self.saw_advertisement == 1 and self.contacts_in_city == 1:
                self.change_children = "migration"
                migrated_agent_ages  = len([l for l in self.ages if (15 <= l <= 35)])
                self.ages = [l for l in self.ages if not (15 <= l <= 35)] # Delete them from the list of ages
                for i in range(migrated_agent_ages):
                    migrated = Migrated(self.model, agent_type = "migrated")
                    self.model.agents.add(migrated)

class Service_workers(Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)

        self.agent_type = agent_type
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.living_costs = 1100 * self.household_size # ASSUMPTION

        # Related to working
        self.working_force = len([num for num in self.ages if 15 <= num <= 59])
        self.original_income = 1100 * self.working_force # ASSUMPTION
        self.income = self.original_income
        self.minimum_income = self.living_costs 
        self.child_who_can_work = 0

        # Related to migrating
        self.contacts_in_city = 0
        self.saw_advertisement = 1
        self.change_children = None
        self.change_leaving_household = 0.1
        self.facilities_in_neighbourhood = 1

        # Related to their own work
        self.assets = random.choice([0,1])
        self.competition = random.randrange(0,10)

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

        # Do you have contacts in the city?
        if random.random() < self.model.migration_ratio and self.contacts_in_city == 0:
            self.contacts_in_city = 1

    def receive_income(self):
        self.income = self.model.reduce_service_income_migrations * self.original_income
        # We need to change as household since the income is too low?
        if self.income < self.minimum_income:
            self.income_too_low = 1
        else:
            self.income_too_low = 0
        self.chance_migration = calculate_migration_ww(self.income_too_low, self.contacts_in_city,  self.facilities_in_neighbourhood)
        if np.random.rand() < self.chance_migration:
            for i in range(len(self.ages)):
                migrated = Migrated(self.model, agent_type = "migrated")
                self.model.agents.add(migrated)
            self.model.agents.remove(self) # Delete the household 

            # Income for another agent should increase, since competition is decreased
            other_service_households = [agent for agent in self.model.agents if isinstance(agent, Service_workers)] # select all service worker agents
            if other_service_households:
                random_agent = random.choice(other_service_households)
                original_competition = random_agent.competition
                random_agent.competition -=1
                if random_agent.competition > 0:
                    random_agent.original_income =random_agent.original_income * (1+ (1/random_agent.competition))
                    
        # What do the young adults/parents want?
        num_children = len([num for num in self.ages if 15 <= num <= 35])
        if np.random.rand() < self.model.chance_leaving_household: # They want to leave
            self.children_possibilities = ["migration"]
            if self.saw_advertisement == 1 and self.contacts_in_city == 1:
                self.change_children = "migration"
                migrated_agent_ages  = len([l for l in self.ages if (15 <= l <= 35)])
                self.ages = [l for l in self.ages if not (15 <= l <= 35)] # Delete them from the list of ages
                for i in range(migrated_agent_ages):
                    migrated = Migrated(self.model, agent_type = "migrated")
                    self.model.agents.add(migrated)
        
# Migrated agents
class Migrated(Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)

        self.agent_type = agent_type

    def step(self):
        pass


                







