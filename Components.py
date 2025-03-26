from mesa import Agent
import numpy as np
import random
from Functions import create_household, die, education_levels, calculate_livelihood_agrifarm,  calculate_cost, calculate_yield, calculate_income_farming, define_abilities, motivation__per_strategy, calculate_MOTA, find_best_strategy, implement_strategy

class Agri_farmer (Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)
        self.agent_type = agent_type
        
    def step(self):
        # Each agent becomes 1 year older
        self.ages = [age + 1 for age in self.ages]

        # Possibility for an agent to die
        self.ages = die(self.ages)

        # Calculate costs based on land size
        self.cost_farming = calculate_cost(self.crop_type, self.seed_quality, self.land_size)

        # Calculate total yield in ton
        self.yield_ = calculate_yield(self.crop_type, self.salinity, self.land_size)

        # Calculate income based on yield and costs
        self.income = calculate_income_farming(self.crop_type, self.seed_quality, self.yield_)
        self.savings += self.income - self.cost_farming - self.cost_living + self.income_benefits

        # Did agrocensus met you this year yes/no?
        self.meeting_agrocensus = 1 if np.random.rand() > 0.56 else 0 # Based on paper Tran et al., (2020)

        # Calculate livelihood
        self.livelihood = calculate_livelihood_agrifarm(self.meeting_agrocensus, self.education_level, self.farming_experience,
        self.community, self.government_support, self.savings, self.loans, self.land_size, self.measures, self.salinity)

        requirements_per_strategy = [{"name": "Drainage", "type": "Water", "price": 1000, "knowledge": 0.7, "technical_ability": 1}, 
        {"name": "Water Reservoir", "type": "Water", "price": 1500, "knowledge": 0.5, "technical_ability": 0},
        {"name": "Crop Diversification", "type": "Crops", "price": 800, "knowledge": 0.6, "technical_ability": 1}]

        if self.possible_strategies:
            # Define technical ability, institutional ability and financial ability
            abilities = define_abilities(self.possible_strategies, requirements_per_strategy, self.savings, self.loan_size, self.livelihood['human'], self.meeting_agrocensus)

            # Define motivation for each strategy
            motivations = motivation__per_strategy(self.possible_strategies, requirements_per_strategy, self.livelihood['financial'], self.livelihood['natural'])

            # Define MOTA score (= ability * motivation) for each strategy
            self.MOTA_scores = calculate_MOTA(motivations, abilities)

            # The strategy with the highest MOTA score will be implemented. If the highest MOTA score is below 0.2, the agent will change nothing (realistic value for 0.2 should be determined later!!)
            self.change = find_best_strategy(self.MOTA_scores)

            # Implement change
            if self.change is not None:
                self.possible_strategies, self.savings = implement_strategy(self.change, self.savings, self.possible_strategies, requirements_per_strategy)
        
        

        



class Agri_small(Agri_farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Agri_small")
        self.income = income

        # Create household
        self.ages = create_household(5,4)        
        self.household_size = len(self.ages)

        self.savings = np.random.normal(2000, 1000) # DETERMINE LATER THE RIGHT SAVINGS FOR A FRAGILE AGRI FARMER
        self.land_size = np.random.normal(1.9, 1) # THIS IS AN ASSUMPTION
        self.cost_farming = 0
        self.cost_living = 1100 * self.household_size # 1100 euro/year/person
        self.income_benefits = 0
        self.yield_ = 0
        self.crop_type = random.choice(['Triple_rice'])
        self.seed_quality = random.choice(['High', "Low"])
        self.salinity = np.random.normal(3, 1) # THIS SHOULD BE DETERMINED LATER
        self.meeting_agrocensus = 0
        self.education_level = education_levels(self)
        self.farming_experience = np.random.normal(0.92, 0.03) # Based on livelihood score farmer experience by Tran et al., (2020) in An Giang, minimum of 5 years experience
        self.community = 0 
        self.government_support = 0
        self.loans = 1 if np.random.rand() > 0.36 else 0 # Based on paper Tran et al., (2020), 0.36% of households get loans
        self.loan_size = 0
        self.measures = [] 
        self.livelihood = 0
        self.possible_strategies = ["Drainage", "Water Reservoir", "Crop Diversification"]
        
    