from mesa import Agent, Model

import numpy as np
import random

class Working_hh_member(Agent):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.education = None

        # Determine the age the agent will die. To prevent the death age is lower than the current age, the max value of death age and currenct age + 1 is taken
        self.death_age = np.random.normal(loc = self.model.excel_data["population_statistics"]['Mean_death_age'], scale = self.model.excel_data["population_statistics"]['Std_dev_death_age'])
        self.death_age = max(self.death_age, self.age+1)

        self.income = 0

    def step(self):
        pass

    def yearly_activities(self):
        self.age += 1
        if self.age >= self.death_age:
            # The agent will die
            self.model.death_agents += 1
            self.model.agents.remove(self)

        # Check if the agent is still working
        if self.works == True:
            if self.age >= 59:
                self.works = self.model.is_working(self.age, self.model.excel_data['work_per_agegroup'])
        

# Individual agents
class Low_skilled_agri_worker(Working_hh_member):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

    def step(self):
        pass

class Low_skilled_nonAgri(Working_hh_member):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Manual_worker(Working_hh_member):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Skilled_agri_worker(Working_hh_member):
    def __init__(self, model, agent_type,age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Skilled_service_worker(Working_hh_member):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

class Other(Working_hh_member):
    def __init__(self, model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model,agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works)
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
        
        self.education = None

        # Determine the age the agent will die. To prevent the death age is lower than the current age, the max value of death age and currenct age + 1 is taken
        self.death_age = np.random.normal(loc = self.model.excel_data["population_statistics"]['Mean_death_age'], scale = self.model.excel_data["population_statistics"]['Std_dev_death_age'])
        self.death_age = max(self.death_age, self.age+1)

    def yearly_activities(self):
        self.age += 1
        if self.age >= self.death_age:
            # The agent will die
            self.model.death_agents += 1
            self.model.agents.remove(self)

        # Updates child education:
        if self.age == 10:
            self.education = "Primary_school"
        elif self.age == 14:
            self.education == "Lower_secondary"
        elif self.age == 17:
            self.education == "Higher_secondary"

        # possibility a child will start working
        if self.age == 15:
            # Out of 16-45, 15% has higher secondary education. There is a change of 15% they will keep studying, otherwise they will start working
            chance_studying = self.model.excel_data['education_levels'][(16,45)]['Higher_secondary']
            if self.random.random() < chance_studying:
                self.works = False
            else:
                self.works = True
                if self.random.random() > self.model.excel_data['sector_distribution']['Non_agri'][1]:
                    # The agent will work in agri sector
                    if self.household.land_area > 0:
                        # Agent will start working on the family farm
                        working_agent = Skilled_agri_worker(self.model, agent_type = "Household_member", age = self.age, agent_sector = self.household.main_crop, agent_occupation = "skilled_agri_worker", agent_employment_type = 'family_worker', assigned = True, works = True)
                    else: # Agent  becomes a wage worker
                        working_agent = Skilled_agri_worker(self.model, agent_type = "Household_member", age = self.age, agent_sector = None, agent_occupation = "skilled_agri_worker", agent_employment_type = 'employee', assigned = True, works = True)
                else:
                    print("lol iets werkt")
                    new_occupation = self.random.choice(['manual_worker', 'skilled_service_worker']) # There is an almost 50/50% chance you will become a manual or skilled service worker, as can be seen in the data bij "Non_agri" and than occupations 
                    agent_classes = {"manual_worker":Manual_worker, 'skilled_service_worker':Skilled_service_worker}
                    agent_class = agent_classes[new_occupation]
                    chance_self_employed = self.model.excel_data['occupation_employment_distribution']['Non_agri'][new_occupation]['employment_distribution']["self_employed"]
                    if self.random.random() < chance_self_employed:
                        employment_type = 'self_employed'
                    else:
                        print('dit gaat goed')
                        employment_type = 'employee'
                    working_agent = agent_class(self.model, agent_type = 'Household_member', age = self.age, agent_sector = 'Non_agri', agent_occupation = new_occupation, agent_employment_type =employment_type, assigned=True, works = True)
                    print("working agent employee is goed gegaan")
                
                # Add working agent to the household, and remove old agent from the household
                working_agent.household = self.household
                # print(self.household.household_members, "before")
                self.household.household_members.remove(self)
                self.household.household_members.append(working_agent)
                # print(self.household.household_members, "after")

                # Update working agent in the model itself
                self.model.agents.add(working_agent)
                self.model.agents.remove(self)
                
                

# Household agents
class Small_land_households(Agent):
    def __init__(self, model,agent_type,  household_size, household_members, land_category, land_area, house_quality, salinity, main_crop, node_id):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality
        self.salinity = salinity
        self.main_crop = main_crop
        self.node_id = node_id

class Middle_land_households(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_category, land_area, house_quality, salinity, main_crop, node_id):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality
        self.salinity = salinity
        self.main_crop = main_crop
        self.node_id = node_id

class Large_land_households(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_category, land_area, house_quality, salinity, main_crop, node_id):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality
        self.salinity = salinity
        self.main_crop = main_crop
        self.node_id = node_id

class Landless_households(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_area, house_quality):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_area = land_area
        self.house_quality = house_quality






