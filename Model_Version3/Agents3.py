from mesa import Agent, Model

import numpy as np
import random

# Individual agents
class Low_skilled_agri_worker(Agent):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

    def step(self):
        print( "yes pikkies")

class Low_skilled_nonAgri(Agent):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Manual_worker(Agent):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Skilled_agri_worker(Agent):
    def __init__(self, model, agent_type,age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Skilled_service_worker(Agent):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Other(Agent):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Non_labourer(Agent):
    def __init__(self, model,agent_type, age, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works


# Household agents
class Small_land_households(Agent):
    def __init__(self, model,agent_type,  household_size, household_members, land_category, land_area, house_quality):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality

class Middle_land_households(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_category, land_area, house_quality):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality

class Large_land_households(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_category, land_area, house_quality):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality

class Landless_households(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_area, house_quality):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_area = land_area
        self.house_quality = house_quality




