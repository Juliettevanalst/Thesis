from mesa import Agent
import numpy as np
import random
from Functions import create_household, die, child_birth, education_levels, calculate_livelihood_agrifarm,  calculate_cost, calculate_yield_agri, calculate_yield_aqua, calculate_income_farming,calculate_income_aqua, calculate_additional_income, calculate_benefits_government, define_abilities, motivation__per_strategy, calculate_MOTA, find_best_strategy, implement_strategy

global requirements_per_strategy
requirements_per_strategy = [{"name": "Drainage", "type": "Water", "price": 1000, "knowledge": 0.7, "technical_ability": 1}, 
{"name": "Water Reservoir", "type": "Water", "price": 1500, "knowledge": 0.5, "technical_ability": 0},
{"name": "Crop Diversification", "type": "Crops", "price": 800, "knowledge": 0.6, "technical_ability": 1}]


class Agri_farmer(Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)
        self.agent_type = agent_type
        
    def step(self):
       pass

    def harvest(self):
        # Calculate costs based on land size
        self.cost_farming += calculate_cost(self.product, self.seed_quality, self.land_size)

        # Calculate total yield in ton
        self.yield_ += calculate_yield_agri(self.product, self.salinity, self.land_size)

        # Calculate income based on yield and costs, and update savings
        self.income += calculate_income_farming(self.product, self.seed_quality, self.yield_)   
        
    def yearly_activities(self):
        # Each agent is one year older
        self.ages = [age + 1 for age in self.ages]

        # Possibility for an agent to die
        self.ages = die(self.ages)

        # Possiblity a child is born
        self.ages = child_birth(self.ages, birth_rate = 0.2, maximum_number_of_children = 6)  # NEED TO CHECK DATA
        
        # Did agrocensus met you this year yes/no?
        self.meeting_agrocensus = 1 if np.random.rand() > 0.56 else 0 # Based on paper Tran et al., (2020)

        # Check if you can get governmental support if your yield is too low, or if you have childs/elderly
        self.government_support, self.additional_income_yield = calculate_additional_income(self.meeting_agrocensus, self.income, self.land_size)
        self.income_benefits = calculate_benefits_government(self.ages)

        # Calculate livelihood
        self.livelihood = calculate_livelihood_agrifarm(self.meeting_agrocensus, self.education_level, self.salt_experience,
        self.community, self.government_support, self.savings, self.loan_size, self.value_of_assets, self.land_size, self.equipment_level, self.salinity)

        #Check if it is possible to change, or if all adaptation and changes have been implemented
        if self.possible_strategies:
            # Define technical ability, institutional ability and financial ability
            abilities = define_abilities(self.possible_strategies, requirements_per_strategy, self.savings, self.loan_size, self.maximal_debt, self.livelihood['human'], self.equipment_level, self.facilities_in_neigbourhood)

            # Define motivation for each strategy
            motivations = motivation__per_strategy(self.possible_strategies, requirements_per_strategy, self.livelihood['financial'], self.livelihood['natural'])

            # Define MOTA score (= ability * motivation) for each strategy
            self.MOTA_scores = calculate_MOTA(motivations, abilities)

            # The strategy with the highest MOTA score will be implemented. 
            self.change = find_best_strategy(self.MOTA_scores)
        
        # If no strategy can be implemented, change will be none
        else:
            self.change = None
            self.MOTA_scores = {}

        # Implement change
        if self.change is not None:
            self.possible_strategies, self.savings, self.loan_size, self.maximal_debt = implement_strategy(self.change, self.savings, self.possible_strategies, requirements_per_strategy, self.loan_size, self.maximal_debt)

        # Update savings
        self.savings += self.income - self.cost_farming - self.cost_living + self.income_benefits + self.additional_income_yield

        # At the end of each year, income should be set to zero
        self.income = 0
        self.cost_farming = 0
        self.yield_ = 0
        

class Agri_small_saline(Agri_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Agri_small_saline")
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)
        self.income = income

        # Create household
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.savings = np.random.normal(2000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.education_level = education_levels(self)
        self.livelihood = 0
        self.community = 0 
        self.government_support = 0
        self.additional_income_yield = 0

        # Define farmer characteristics
        self.land_size = np.random.normal(1.9, 1) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.yield_ = 0
        self.product = np.random.choice(['Triple_rice'])
        self.seed_quality = np.random.choice(['High', "Low"])
        self.salinity = np.random.normal(4, 1) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.salt_experience = 1 
        self.wage_workers = np.random.choice([0,1])
        
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300)
        self.value_of_assets = self.land_size * 3000 + self.house_price # Value of assets depends on land size and the value of the house
        self.maximal_debt = self.value_of_assets
        self.equipment_level = np.random.normal(0.3,0.1) # This one will increase if you adaptate measures BASED ON NOTHING
        self.facilities_in_neigbourhood = 1
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"] # These will be changed later when actual changes are identified
        self.MOTA_scores = {}

class Agri_small_fresh(Agri_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Agri_small_fresh")
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)
        self.income = income

        # Create household
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.savings = np.random.normal(4000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.education_level = education_levels(self)
        self.livelihood = 0
        self.community = 0 
        self.government_support = 0
        self.additional_income_yield = 0

        # Define farmer characteristics
        self.land_size = np.random.normal(1.9, 1) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.yield_ = 0
        self.product = np.random.choice(['Triple_rice'])
        self.seed_quality = np.random.choice(['High', "Low"])
        self.salinity = np.random.normal(2, 0.5) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.salt_experience = 0
        self.wage_workers = np.random.choice([0,1])
        
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300)
        self.value_of_assets = self.land_size * 3000 + self.house_price # Value of assets depends on land size and the value of the house
        self.maximal_debt = self.value_of_assets
        self.equipment_level = np.random.normal(0.3,0.1) # This one will increase if you adaptate measures BASED ON NOTHING
        self.facilities_in_neigbourhood = 1
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"] # These will be changed later when actual changes are identified
        self.MOTA_scores = {}

class Agri_middle_saline(Agri_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Agri_middle_saline")
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)
        self.income = income

        # Create household
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.savings = np.random.normal(4000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.education_level = education_levels(self)
        self.livelihood = 0
        self.community = 0 
        self.government_support = 0
        self.additional_income_yield = 0

        # Define farmer characteristics
        self.land_size = np.random.normal(4, 1) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.yield_ = 0
        self.product = np.random.choice(['Triple_rice'])
        self.seed_quality = np.random.choice(['High', "Low"])
        self.salinity = np.random.normal(4,1) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.salt_experience = 1
        self.wage_workers = np.random.randint(0,3)
        
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300)
        self.value_of_assets = self.land_size * 3000 + self.house_price # Value of assets depends on land size and the value of the house
        self.maximal_debt = self.value_of_assets
        self.equipment_level = np.random.normal(0.3,0.1) # This one will increase if you adaptate measures BASED ON NOTHING
        self.facilities_in_neigbourhood = 1
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"] # These will be changed later when actual changes are identified
        self.MOTA_scores = {}

class Agri_middle_fresh(Agri_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Agri_middle_fresh")
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)
        self.income = income

        # Create household
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.savings = np.random.normal(4000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.education_level = education_levels(self)
        self.livelihood = 0
        self.community = 0 
        self.government_support = 0
        self.additional_income_yield = 0

        # Define farmer characteristics
        self.land_size = np.random.normal(4, 1) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.yield_ = 0
        self.product = np.random.choice(['Triple_rice'])
        self.seed_quality = np.random.choice(['High', "Low"])
        self.salinity = np.random.normal(2, 0.5) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.salt_experience = 0
        self.wage_workers = np.random.randint(0,3)
        
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300)
        self.value_of_assets = self.land_size * 3000 + self.house_price # Value of assets depends on land size and the value of the house
        self.maximal_debt = self.value_of_assets
        self.equipment_level = np.random.normal(0.3,0.1) # This one will increase if you adaptate measures BASED ON NOTHING
        self.facilities_in_neigbourhood = 1
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"] # These will be changed later when actual changes are identified
        self.MOTA_scores = {}
        
class Agri_corporate_saline(Agri_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Agri_corporate_saline")
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)
        self.income = income

        # Create household
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.savings = np.random.normal(4000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.education_level = education_levels(self)
        self.livelihood = 0
        self.community = 0 
        self.government_support = 0
        self.additional_income_yield = 0

        # Define farmer characteristics
        self.land_size = np.random.normal(10, 4) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.yield_ = 0
        self.product = np.random.choice(['Triple_rice'])
        self.seed_quality = np.random.choice(['High', "Low"])
        self.salinity = np.random.normal(4,1) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.salt_experience = 1
        self.wage_workers = np.random.randint(2,8)
        
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300)
        self.value_of_assets = self.land_size * 3000 + self.house_price # Value of assets depends on land size and the value of the house
        self.maximal_debt = self.value_of_assets
        self.equipment_level = np.random.normal(0.3,0.1) # This one will increase if you adaptate measures BASED ON NOTHING
        self.facilities_in_neigbourhood = 1
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"] # These will be changed later when actual changes are identified
        self.MOTA_scores = {}

        
class Agri_corporate_fresh(Agri_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Agri_corporate_fresh")
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)
        self.income = income

        # Create household
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.savings = np.random.normal(4000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.education_level = education_levels(self)
        self.livelihood = 0
        self.community = 0 
        self.government_support = 0
        self.additional_income_yield = 0

        # Define farmer characteristics
        self.land_size = np.random.normal(10, 4) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.yield_ = 0
        self.product = np.random.choice(['Triple_rice'])
        self.seed_quality = np.random.choice(['High', "Low"])
        self.salinity = np.random.normal(2, 0.5) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.salt_experience = 0
        self.wage_workers = np.random.randint(2,8)
        
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300)
        self.value_of_assets = self.land_size * 3000 + self.house_price # Value of assets depends on land size and the value of the house
        self.maximal_debt = self.value_of_assets
        self.equipment_level = np.random.normal(0.3,0.1) # This one will increase if you adaptate measures BASED ON NOTHING
        self.facilities_in_neigbourhood = 1
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"] # These will be changed later when actual changes are identified
        self.MOTA_scores = {}

# CREATE AQUA FARMERS   
class Aqua_farmer (Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)
        self.agent_type = agent_type
        
        
    def step(self):
           pass

    def harvest(self):
        # Calculate costs based on land size
        self.cost_farming += calculate_cost(self.product, self.feeding_quality, self.land_size)

        # Calculate total yield in ton
        self.yield_ += calculate_yield_aqua(self.product, self.farm_type, self.water_quality, self.disease, self.land_size)

        # Calculate income based on yield and costs, and update savings
        self.income += calculate_income_aqua(self.product, self.farm_type, self.yield_) 
    
    def yearly_activities(self):
        self.ages = [age + 1 for age in self.ages]

        # Possibility for an agent to die
        self.ages = die(self.ages)

        # Possiblity a child is born
        self.ages = child_birth(self.ages, birth_rate = 0.2, maximum_number_of_children = 6)  # NEED TO CHECK DATA
        
        # Did agrocensus met you this year yes/no?
        self.meeting_agrocensus = 1 if np.random.rand() > 0.56 else 0 # Based on paper Tran et al., (2020)

        # Chance you have a disease
        self.disease = random.choice([0,1])

        

        # Check if you can get governmental support if your yield is too low, or if you have childs/elderly
        # self.government_support, self.additional_income_yield = calculate_additional_income(self.meeting_agrocensus, self.income, self.land_size)
        # self.income_benefits = calculate_benefits_government(self.ages)

        # Calculate livelihood
        self.livelihood = calculate_livelihood_agrifarm(self.meeting_agrocensus, self.education_level, self.experience,
        self.community, self.government_support, self.savings, self.loan_size, self.value_of_assets, self.land_size, self.equipment_level, self.salinity)

        #Check if it is possible to change, or if all adaptation and changes have been implemented
        if self.possible_strategies:
            # Define technical ability, institutional ability and financial ability
            abilities = define_abilities(self.possible_strategies, requirements_per_strategy, self.savings, self.loan_size, self.maximal_debt, self.livelihood['human'], self.equipment_level, self.facilities_in_neigbourhood)

            # Define motivation for each strategy
            motivations = motivation__per_strategy(self.possible_strategies, requirements_per_strategy, self.livelihood['financial'], self.livelihood['natural'])

            # Define MOTA score (= ability * motivation) for each strategy
            self.MOTA_scores = calculate_MOTA(motivations, abilities)

            # The strategy with the highest MOTA score will be implemented. 
            self.change = find_best_strategy(self.MOTA_scores)
        
        # If no strategy can be implemented, change will be none
        else:
            self.change = None
            self.MOTA_scores = {}

        # Implement change
        if self.change is not None:
            self.possible_strategies, self.savings, self.loan_size, self.maximal_debt = implement_strategy(self.change, self.savings, self.possible_strategies, requirements_per_strategy, self.loan_size, self.maximal_debt)

        # Update savings
        self.savings += self.income - self.cost_farming - self.cost_living + self.income_benefits + self.additional_income_yield

         # At the end of each year, income should be set to zero
        self.income = 0
        self.cost_farming = 0
        self.yield_ = 0
        

class Aqua_small(Aqua_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Aqua_small")
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)
        self.income = income

        # Create household
        self.ages = create_household(5,2)        
        self.household_size = len(self.ages)
        self.savings = np.random.normal(2000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.education_level = education_levels(self)
        self.livelihood = 0
        self.community = 0 
        self.government_support = 0
        self.additional_income_yield = 0

        # Define farmer characteristics
        self.land_size = np.random.normal(1.9, 1) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.yield_ = 0
        self.product = np.random.choice(['Shrimp'])
        self.feeding_quality = np.random.choice(['High', "Low"])
        self.water_quality = 1 # THIS SHOULD CHANGE LATER, THE BEST STIUATION IS 1 BUT IT WILL WORSEN OVER TIME
        self.farm_type = np.random.choice(['Extensive', 'Intensive'])
        self.salinity = np.random.normal(4, 1) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.disease = 0
        self.experience = 1 # THIS IS AN ASSUMPTION, THAT EVERY FARMER IS ALREADY EXPERIENCED
        self.wage_workers = np.random.choice([0,1])
        
        self.loan_size = 0
        self.house_price = np.random.normal(2000, 300)
        self.value_of_assets = self.land_size * 3000 + self.house_price # Value of assets depends on land size and the value of the house
        self.maximal_debt = self.value_of_assets
        self.equipment_level = np.random.normal(0.3,0.1) # This one will increase if you adaptate measures BASED ON NOTHING
        self.facilities_in_neigbourhood = 1
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"] # These will be changed later when actual changes are identified
        self.MOTA_scores = {}



        
    