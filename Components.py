from mesa import Agent
import numpy as np
import random
from Functions import yield_productivity, calculate_income

class Farmer (Agent):
    def __init__(self, model, agent_type):
        super().__init__(model)
        self.agent_type = agent_type
        
    def step(self):
        pass

class Fragile_agri(Farmer):
    def __init__(self, model, agent_type, income = 0):
        super().__init__(model, "Fragile_agri")
        self.income = income
        self.savings = np.random.normal(53000, 20000) # DETERMINE LATER THE RIGHT INCOME FOR A FRAGILE AGRI FARMER
        self.land = np.random.normal(20000, 5000) # DETERMINE LATER THE RIGHT AMOUNT OF LAND IN M2
        self.cost = 0
        self.yield_ = 0
        self.seeds = 400 # in kg
        self.crop_type = random.choice(['High_quality_rice', 'Low_quality_rice'])

    def calculate_yield(self):
        # TO DO: Calculate salinity levels
        total_yield = self.seeds * self.land * yield_productivity(self.crop_type)
        return total_yield
        

    def step(self):
        total_yield = self.calculate_yield()
        yearly_income = calculate_income(self.crop_type, total_yield)
        self.income = yearly_income
        self.savings += self.income

