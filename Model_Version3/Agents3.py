from mesa import Agent, Model

import numpy as np
import random
import statistics

from Functions3 import get_education_levels, get_experience, get_dissabilities, get_association, calculate_livelihood, calculate_yield_agri
from Functions3 import calculate_farming_costs, calculate_yield_shrimp, calculate_cost_shrimp, calculate_wages_farm_workers, calculate_total_income, advice_neighbours, advice_agrocensus
from Functions3 import define_abilities, define_motivations, calculate_MOTA, best_MOTA, annual_loan_payment, change_crops
from Functions3 import calculate_migration_ww, household_experience_machines


class Working_hh_member(Agent):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.education = get_education_levels(self.age, self.model)
        # self.household = household

        # Determine the age the agent will die. To prevent the death age is lower than the current age, the max value of death age and currenct age + 1 is taken
        self.death_age = np.random.normal(
            loc=self.model.excel_data["population_statistics"]['Mean_death_age'], scale=(self.model.excel_data["population_statistics"]['Std_dev_death_age'])/3) # ik heb deze std door twee gedaan anders gingen mensen veel te snel dood
        self.death_age = max(self.death_age, self.age+1)

        self.income = 0
        self.experience, self.machines = get_experience(
            self.agent_occupation, self.model)
        self.dissabilities = get_dissabilities(self.age, self.model)
        self.time_since_last_income = 0

    def step(self):
        pass

    def yearly_activities(self):
        self.age += 1
        if self.age >= self.death_age:
            # The agent will die
            self.model.death_agents += 1
            self.household.household_size -= 1
            if self in self.household.household_members:
                self.household.household_members.remove(self)
            self.model.agents.remove(self)

        # Check if the agent is still working
        if self.works == True:
            if self.age >= 59:
                self.works = self.model.is_working(
                    self.age, self.model.excel_data['work_per_agegroup'])


# Individual agents
class Low_skilled_agri_worker(Working_hh_member):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model, agent_type, age, agent_sector,
                         agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.income = 0
        self.time_since_last_income = 0

    def step(self):
        pass


class Low_skilled_nonAgri(Working_hh_member):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model, agent_type, age, agent_sector,
                         agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.income = 0


class Manual_worker(Working_hh_member):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model, agent_type, age, agent_sector,
                         agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.income = 0


class Skilled_agri_worker(Working_hh_member):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model, agent_type, age, agent_sector,
                         agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.income = 0


class Skilled_service_worker(Working_hh_member):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model, agent_type, age, agent_sector,
                         agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.income = 0


class Other(Working_hh_member):
    def __init__(self, model, agent_type, age, agent_sector, agent_occupation, agent_employment_type, assigned, works):
        super().__init__(model, agent_type, age, agent_sector,
                         agent_occupation, agent_employment_type, assigned, works)
        self.agent_type = agent_type
        self.age = age
        self.agent_sector = agent_sector
        self.agent_occupation = agent_occupation
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.income = 0


class Non_labourer(Agent):
    def __init__(self, model, agent_type, age, agent_employment_type, assigned, works):
        super().__init__(model)
        self.agent_type = agent_type
        self.age = age
        self.agent_employment_type = agent_employment_type
        self.assigned = assigned
        self.works = works

        self.income = 0

        # self.household = household
        # Define education. For children, the education distribution will be based on their age
        self.education = get_education_levels(self.age, self.model)
        if self.age < 6:
            self.education = "no_schooling"
        elif self.age < 10:
            self.education = "below_primary"
        elif self.age < 14:
            self.education = "Primary_school"
        elif self.age < 17:
            self.education == "Lower_secondary"
        elif self.age == 17:
            self.education == "Higher_secondary"

        # Determine the age the agent will die. To prevent the death age is lower than the current age, the max value of death age and currenct age + 1 is taken
        self.death_age = np.random.normal(
            loc=self.model.excel_data["population_statistics"]['Mean_death_age'], scale=(self.model.excel_data["population_statistics"]['Std_dev_death_age'])/3) # ik heb deze std door twee gedaan anders gingen mensen veel te snel dood
        self.death_age = max(self.death_age, self.age+self.random.uniform(1,5)) # If they are older than their death age, they will die somewhere in the next five  years

        # Even when they are not working, they can be a member of an association and can have difficulties
        self.experience = 0
        self.machines = 0
        self.dissabilities = get_dissabilities(self.age, self.model)

    def yearly_activities(self):
        self.age += 1
        if self.age >= self.death_age:
            # The agent will die
            self.model.death_agents += 1
            self.household.household_size -= 1
            if self in self.household.household_members:
                self.household.household_members.remove(self)
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
            chance_studying = self.model.excel_data['education_levels'][(
                16, 45)]['Higher_secondary']
            if self.random.random() < chance_studying:
                self.works = False
            else:
                self.works = True
                self.start_working()

        elif self.age == 17:
            works = self.model.is_working(self.age, self.model.excel_data['work_per_agegroup'])
            if works:
                self.start_working()


    def start_working(self):
        if self.random.random() > self.model.excel_data['sector_distribution']['Non_agri'][1]:
            # The agent will work in agri sector
            if self.household.land_area > 0:
                # Agent will start working on the family farm
                working_agent = Skilled_agri_worker(self.model, agent_type="Household_member", age=self.age, agent_sector=self.household.crop_type,
                                                    agent_occupation="skilled_agri_worker", agent_employment_type='family_worker', assigned=True, works=True)
            else:  # Agent  becomes a wage worker
                working_agent = Skilled_agri_worker(self.model, agent_type="Household_member", age=self.age, agent_sector=None,
                                                    agent_occupation="skilled_agri_worker", agent_employment_type='employee', assigned=True, works=True)
        else:
            # There is an almost 50/50% chance you will become a manual or skilled service worker, as can be seen in the data bij "Non_agri" and then occupations
            new_occupation = self.random.choice(
                ['manual_worker', 'skilled_service_worker'])
            agent_classes = {"manual_worker": Manual_worker,
                                'skilled_service_worker': Skilled_service_worker}
            agent_class = agent_classes[new_occupation]
            chance_self_employed = self.model.excel_data['occupation_employment_distribution'][
                'Non_agri'][new_occupation]['employment_distribution']["self_employed"]
            if self.random.random() < chance_self_employed:
                employment_type = 'self_employed'
            else:
                employment_type = 'employee'
            working_agent = agent_class(self.model, agent_type='Household_member', age=self.age, agent_sector='Non_agri',
                                        agent_occupation=new_occupation, agent_employment_type=employment_type, assigned=True, works=True)

        # Add working agent to the household, and remove old agent from the household
        working_agent.household = self.household
        if self in self.household.household_members:
            self.household.household_members.remove(self)
        self.household.household_members.append(working_agent)

        # Update working agent in the model itself
        self.model.agents.add(working_agent)
        self.model.agents.discard(self)

# Household agents
class Land_household(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_category, land_area, house_quality):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality

        self.salinity_during_shock = 0

        # self.growth_time = {}
        self.possible_next_crops = None
        self.new_crop = None

        self.house_price = np.random.normal(52000000)  # ASSUMPTION!!
        self.value_of_assets = self.land_area * \
            78000000 + self.house_price  # ASSUMPTION
        self.maximum_debt = self.value_of_assets
        self.debt = 0
        self.yearly_loan_payment = 0
        self.wage_worker_payment = 0

        self.savings = 10000000  # ASSUMPTION!!
        self.total_cost_farming_ = {}
        self.wage_costs_ = {}
        self.total_income_ = {}
        self.yearly_income = 0
        self.percentage_yield_ = {}
        self.expenditure = 0
        for agent in household_members:
            if agent.age < 16:
                self.expenditure += 1755000
            else:
                self.expenditure += 2599000
        self.required_income = self.expenditure
        self.information_meeting = 0
        self.association = get_association(self.model)

        self.MOTA_scores = None
        self.new_crop = None
        self.waiting_time = 0
        self.livelihood = {"Human": 0, "Social": 0, "Financial": 0,
                           "Physical": 0, "Natural": 0, "Average": 0}

        self.use_antibiotics = 0
        self.crop_history = {"Rice":0, "Shrimp":0, "Coconut":0, "Maize":0}

        # Identify if the household has experience and machines
        self.machines, self.experience = household_experience_machines(self.household_members)
        self.average_hh_experiences = (self.experience + self.machines) / 2

        self.saw_advertisement = 0
        self.contacts_in_city = 0
        self.facilities_in_neighbourhood = 1

    def step(self):
        if self.household_size == 0:
            self.model.agents.remove(self)
            # print("household died")

    def yearly_activities(self):
        # If the whole household is death, the household will be removed from the model
        if not self.household_members:
            self.model.deceased_households += 1
            # Remove the agent from the model
            self.model.agents.discard(self)
        

        # Possibility for birth
        # I took the birth rate of the whole population, not only women
        birth_rate_mekong = self.model.excel_data["population_statistics"]['Birth_rate'] * \
            self.household_size
        if self.random.random() <= birth_rate_mekong:
            # A child is born!
            new_child = Non_labourer(self.model, agent_type='Household_member',
                                     age=0, agent_employment_type=None, assigned=True, works=False)
            self.model.child_births += 1                                     
            self.model.agents.add(new_child)
            self.household_members.append(new_child)
            self.household_size += 1
            new_child.household = self

        if self.random.random() > self.model.chance_info_meeting:
            self.information_meeting = 1
        else:
            self.information_meeting = 0

        # Update savings and debt
        self.savings -= self.yearly_loan_payment
        self.savings = self.savings * (self.model.interest_rate_savings + 1)
        self.debt = self.debt * (self.model.interest_rate_loans + 1)

    def harvest(self, crop):
        land_area = self.crops_and_land[crop]
        growth_times = {"Rice": 3,  "Maize": 4, "Coconut": 0, "Shrimp": 6}
        # if a shock happened during growth time, we need to take that salinity into account, otherwise, current salinity
        if self.model.time_since_shock > growth_times[crop]:
            self.salinity_during_shock = self.salinity

        if crop == "Shrimp":
            # Did you get a disease this season?
            self.disease = 1 if np.random.rand() <= self.model.chance_disease else 0

            # Do you want to use antibiotics? D
            if self.disease == 1:
                # THIS IS AN ASSUMPTION, IF YOU ARE SMART YOU WILL NOT USE ANTIBIOTICS
                if (self.livelihood['Human']+self.livelihood['Financial'])/2 >= 0.5:
                    # Use no antibiotics
                    self.use_antibiotics = 0
                    self.percentage_yield_["Shrimp"] = 0.26 # 37/140 = 0.26, only 26% of your fish survives
                else:
                    self.use_antibiotics = 1
            else:
                self.use_antibiotics = 0
                self.percentage_yield_["Shrimp"] = 1
            self.yield_["Shrimp"] = calculate_yield_shrimp(
                land_area, self.disease, self.use_antibiotics)
            self.total_cost_farming_["Shrimp"] = calculate_cost_shrimp(
                land_area, self.use_antibiotics)
            self.percentage_yield_["Shrimp"] = 1

        else:
            # Calculate yield
            self.yield_[crop], self.percentage_yield_[crop] = calculate_yield_agri(
                crop, land_area, self.salinity, self.livelihood['Human'], self.percentage_yield_)

            # Calculate cost farming
            self.total_cost_farming_[
                crop] = calculate_farming_costs(crop, land_area)

        # Calculate costs wage costs + determine number of wage workers you had during yield time
        self.wage_costs_[crop], self.wage_workers = calculate_wages_farm_workers(
            crop, land_area, self.household_members, self.model, self.machines, self.percentage_yield_[crop])

        if crop == "Maize": # There is a lack of maize data, therefore somethings wage costs are higher than total costs in my model for maize. I decided to solve this by taking Maize, and adding "vaste kosten" of 6.8 million
            self.total_cost_farming_[crop] = self.wage_costs_[crop] + self.model.maize_fixed_costs * land_area

        # calculate total income based on yield and costs
        self.total_income_[crop] = calculate_total_income(
            crop, self.yield_[crop], self.total_cost_farming_[crop])
        if crop == "Rice":
            self.yearly_income = self.total_income_[crop] * 3
        elif crop == "Shrimp" or crop == "Maize":
            self.yearly_income = self.total_income_[crop] * 2
        else:
            self.yearly_income = self.total_income_[crop] * 6

        if self.total_income_[crop] < 0:
            print(crop)
        #     print("dit kan dus niet")
            # print("mijnl and  is ", land_area)
            # print("mijn yield  is: ", self.yield_[crop])
            # print(self.wage_costs_[crop], " zijn de kosten van wage")
            # print(self.total_cost_farming_[crop], " zijn de kosten totaal van ", crop)
            # print(self.total_income_[crop], " totale inkomen van ", crop)
            # print(self.machines, " huishouden heeft wel/geen machine")

        # update savings
        self.savings += self.total_income_[crop]

    def check_savings(self):
        total_income_all_crops = sum(self.total_income_.values())
        total_wage_income = 0
        for agent in self.household_members:
            total_wage_income += agent.income
        self.total_hh_income = total_income_all_crops + total_wage_income
        if "Rice" in self.crops_and_land.keys():
            time_frame = 3
        elif "Maize" in self.crops_and_land.keys() or "Shrimp" in self.crops_and_land.keys():
            time_frame = 6
        else:
            time_frame = 2  # you do coconut

        expenditure = self.expenditure / 12 * time_frame
        self.monthly_hh_income = self.total_hh_income / time_frame
        self.savings += self.total_hh_income - expenditure

        for agent in self.household_members:
            agent.income = 0

    def check_changes(self):
        self.prepare_livelihood()
        self.livelihood = calculate_livelihood(self.information_meeting, self.average_hh_education, self.average_hh_experiences, self.dissability,
                                               self.model.current_hh_left, self.association, self.savings, self.debt_ratio, self.land_ratio, 
                                               self.house_quality, self.salinity_suitability)
        if self.livelihood['Average'] < 0.3:  # ASSUMPTION!!!!
            print("land household migrated")
            self.model.agents_to_remove.append(self)

        if self.waiting_time == 0:  # You cannot change if your coconuts are still growing
            if "Shrimp" in self.crops_and_land.keys():
                # You cannot switch back to another crop, due to the high salinity and antibiotics in the land.
                self.possible_next_crops = ["Shrimp"]
            else:
                # Decide on next crop
                self.possible_next_crops = []
                # Check if there is advice from agrocensus meeting you attended
                if self.information_meeting == 1:
                    self.possible_next_crops.extend(advice_agrocensus(
                        self.salinity, self.average_hh_education, list(self.crops_and_land.keys())))
                # It is always possible to  keep the current crop
                self.possible_next_crops.extend(
                    list(self.crops_and_land.keys()))
                # Check what your neighbors are doing
                self.possible_next_crops = advice_neighbours(
                    self.possible_next_crops, self.model, self.node_id)
                # Check your abilities per possible crop:
                current_largest_crop = max(
                    self.crops_and_land, key=self.crops_and_land.get)
                current_crops = list(self.crops_and_land.keys())
                self.abilities = define_abilities(self.possible_next_crops, self.savings, self.debt, self.maximum_debt,
                                                  self.livelihood['Human'], self.salinity, current_largest_crop, self.land_area, self.machines)
                # Check your motivations per possible crop:
                self.motivations = define_motivations(
                    self.possible_next_crops, self.yearly_income, self.abilities, current_largest_crop, self.required_income, self.land_area)
                # Calculate MOTA scores and find the best crop:
                self.MOTA_scores = calculate_MOTA(
                    self.motivations, self.abilities)
                self.new_crop = best_MOTA(
                    self.MOTA_scores, current_largest_crop)
                # Implement possible change
                if self.new_crop not in list(self.crops_and_land.keys()):
                    self.savings, self.debt, self.maximum_debt, self.crops_and_land, self.waiting_time, self.crop_type = change_crops(
                        self.new_crop, self.savings, self.debt, self.maximum_debt, self.land_area, current_largest_crop, current_crops)
                    
                    self.yearly_loan_payment = annual_loan_payment(
                        self.debt, self.model.interest_rate_loans)

        # Do the young adults (15-35) want to migrate?
        possible_migrated_members = [
            agent for agent in self.household_members if agent.age > 15 and agent.age < 35]
        if len(possible_migrated_members) > 0:
            chance_migrating = self.model.chance_leaving_household
            if self.saw_advertisement == 1 and self.contacts_in_city == 1:
                chance_migrating += self.model.increased_chance_migration_familiarity # ASSUMPTION
            if self.random.random() < chance_migrating:  # They want to leave
                for agent in possible_migrated_members:
                    self.model.agents_become_migrated_members.append(agent)

    def update_experience(self):
        # Each year, experience should increase
        for crop in self.crops_and_land.keys():
            self.crop_history[crop] += 1

    def prepare_livelihood(self):
        # average_education
        education_levels = []
        for agent in self.household_members:
            if agent.age > 15:  # Otherwise you also get the no education of the childs
                education = agent.education
                if education == 'no_schooling' or education == 'below_primary':
                    education_levels.append(0)
                elif education == "primary_education":
                    education_levels.append(0.5)
                else:
                    # SENSITIVITY ANALYSIS IS REQUIRED FOR THE 0, 0.5 AND 1
                    education_levels.append(1)
        if len(education_levels) == 0:
            education_levels = [0]  # DE DEATH RATE STAAT TE HOOG
            
        self.average_hh_education = statistics.mean(education_levels)

        # Define experience based on experiences on the land and use of machines
        experience = 0
        for crop in self.crops_and_land.keys():
            if self.crop_history[crop] >= 3:
                experience = 1
            else:
                experience = 0
                break

        if experience == 1:
            self.experience = 1
        else:
            self.experience = self.experience
        self.average_hh_experiences = (self.experience + self.machines)/2
        

        # Dissabilities
        dissability_list = []
        for agent in self.household_members:
            dissability = agent.dissabilities
            dissability_list.append(dissability)
        # one person with dissability = 0.5, more than 1 your dissabilities = 0
        if sum(dissability_list) < 1:
            self.dissability = 0
        elif sum(dissability_list) == 1:
            self.dissability = 0.5
        else:
            self.dissability = 1

        # Check debt ratio
        if self.debt / self.value_of_assets > 1:
            print("dit gaat mis")
        self.debt_ratio = min(self.debt / self.maximum_debt, 1)

        # check land size
        if self.land_category == 'small':
            self.land_ratio = self.land_area / 0.5
        elif self.land_category == "medium":
            self.land_ratio = self.land_area / 2
        elif self.land_category == 'large':
            # These are the maximum values per category as defined in def get_land_area in model3.py
            self.land_ratio = self.land_area / 5

        # Check salinity level
        largest_crop = max(self.crops_and_land, key=self.crops_and_land.get)
        if largest_crop == "Shrimp" or largest_crop == "Coconut":
            self.salinity_suitability = 1
        elif largest_crop == "Rice":
            if 0 <= self.salinity <= 3:  # So you do not waste yield on salinity
                self.salinity_suitability = 1
            elif self.salinity <= 6:  # So you have 75% of your yield
                self.salinity_suitability = 0.5
            else:
                self.salinity_suitability = 0
        elif largest_crop == "Maize":
            if 0 <= self.salinity <= 1.7:  # So you do not waste yield on salinity
                self.salinity_suitability = 1
            elif self.salinity <= 4.2:  # So you have 75% of your yield
                self.salinity_suitability = 0.5
            else:
                self.salinity_suitability = 0

class Small_land_households(Land_household):
    def __init__(self, model, agent_type,  household_size, household_members, land_category, land_area, house_quality, salinity, crop_type, node_id):
        super().__init__(model, agent_type, household_size,
                         household_members, land_category, land_area, house_quality)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality
        self.salinity = salinity
        self.crop_type = crop_type
        self.node_id = node_id

        global sector_crop_dict
        sector_crop_dict = {'Annual crops': 'Maize', "Aquaculture": "Shrimp",
                            "Perennial crops": "Coconut", "Other agriculture": "Rice"}
        self.crops = []
        self.crops.append(sector_crop_dict[self.crop_type])
        self.crops_and_land = {}
        self.crops_and_land = {self.crops[0]: self.land_area}
        self.growth_time = {self.crops[0]: 0}

        self.yield_ = {}


class Middle_land_households(Land_household):
    def __init__(self, model, agent_type, household_size, household_members, land_category, land_area, house_quality, salinity, crop_type, node_id):
        super().__init__(model, agent_type, household_size,
                         household_members, land_category, land_area, house_quality)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality
        self.salinity = salinity
        self.crop_type = crop_type
        self.node_id = node_id

        sector_crop_dict = {'Annual crops': 'Maize', "Aquaculture": "Shrimp",
                            "Perennial crops": "Coconut", "Other agriculture": "Rice"}
        self.crops = []
        self.crops.append(sector_crop_dict[self.crop_type])
        self.crops_and_land = {}
        self.crops_and_land = {self.crops[0]: self.land_area}
        self.growth_time = {self.crops[0]: 0}

        self.yield_ = {}


class Large_land_households(Land_household):
    def __init__(self, model, agent_type, household_size, household_members, land_category, land_area, house_quality, salinity, crop_type, node_id):
        super().__init__(model, agent_type, household_size,
                         household_members, land_category, land_area, house_quality)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_category = land_category
        self.land_area = land_area
        self.house_quality = house_quality
        self.salinity = salinity
        self.crop_type = crop_type
        self.node_id = node_id

        sector_crop_dict = {'Annual crops': 'Maize', "Aquaculture": "Shrimp",
                            "Perennial crops": "Coconut", "Other agriculture": "Rice"}
        self.crops = []
        self.crops.append(sector_crop_dict[self.crop_type])
        self.crops_and_land = {}
        self.crops_and_land = {self.crops[0]: self.land_area}
        self.growth_time = {self.crops[0]: 0}

        self.yield_ = {}


class Landless_households(Agent):
    def __init__(self, model, agent_type, household_size, household_members, land_area, house_quality):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_size = household_size
        self.household_members = household_members
        self.land_area = land_area
        self.house_quality = house_quality

        self.house_price = np.random.normal(52000000, 7800000)  # ASSUMPTION!!
        self.value_of_assets = self.house_price
        self.maximum_debt = self.value_of_assets

        self.debt = 0
        self.savings = 10000000  # ASSUMPTION!!

        self.expenditure = 0
        for agent in household_members:
            if agent.age < 16:
                self.expenditure += 1755000
            else:
                self.expenditure += 2599000

        self.contacts_in_city = 0
        self.facilities_in_neighbourhood = 1
        self.migrating = False
        self.saw_advertisement = 0

    def yearly_activities(self):
        if not self.household_members:
            self.model.deceased_households += 1
            # Remove the agent from the model
            print(self.model.deceased_households)
            self.model.agents.discard(self)

        # Possibility for birth
        # I took the birth rate of the whole population, not only women
        birth_rate_mekong = self.model.excel_data["population_statistics"]['Birth_rate'] * \
            self.household_size
        if self.random.random() <= birth_rate_mekong:
            # A child is born!
            new_child = Non_labourer(self.model, agent_type='Household_member',
                                     age=0, agent_employment_type=None, assigned=True, works=False)
            self.model.child_births += 1
            self.model.agents.add(new_child)
            self.household_members.append(new_child)
            self.household_size += 1
            new_child.household = self

        # Receive interest based on interest rate
        self.savings = self.savings * (self.model.interest_rate_savings + 1)

        # Check if you have contacts in the city
        if self.random.random() < self.model.current_hh_left and self.contacts_in_city == 0:
            self.contacts_in_city = 1

        # Check facilities in neighborhood
        self.facilities_in_neighbourhood = self.model.current_service_workers / \
            self.model.start_service_workers

    def check_income(self, time_since_income):
        total_wage_income = 0
        for agent in self.household_members:
            total_wage_income += agent.income
        self.total_hh_income = total_wage_income
        time_frame = time_since_income

        expenditure = self.expenditure / 12 * time_frame
        self.monthly_hh_income = self.total_hh_income / time_frame
        self.savings += self.total_hh_income - expenditure
        # # zijn er jonge mensen die weg willen van de farm? --> DIT MOETEN DE LAND HOUSEHOLDS OOK NOG HEBBEN

        if self.total_hh_income < expenditure:
            self.income_too_low = 1
        else:
            self.income_too_low = 0

        # Are we migrating?
        self.chance_migration = calculate_migration_ww(
            self.model, self.income_too_low, self.contacts_in_city,  self.facilities_in_neighbourhood)
        if self.random.random() < self.chance_migration:
            self.migrating = True
            self.model.agents_to_remove.append(self)

        if self.income_too_low == 1 and self.migrating == False:
            # Can we switch to manual or other work?
            low_skilled_agents = [agent for agent in self.household_members if isinstance(
                agent, (Low_skilled_agri_worker, Low_skilled_nonAgri))]
            manual_other_agents = [agent for agent in self.household_members if isinstance(
                agent, (Manual_worker, Other))]
            if len(low_skilled_agents) > 0 and len(manual_other_agents) > 0:
                for agent in low_skilled_agents:
                    low_skilled_income = agent.income
                    break
                for agent in manual_other_agents:
                    manual_other_income = agent.income
                if manual_other_income > low_skilled_income:
                    # Switch to manual_other_income
                    for agent in low_skilled_agents:
                        self.model.agents_become_manual.append(agent)
                else:
                    for agent in manual_other_agents:
                        self.model.agents_become_low_skilled_farm.append(agent)
            # If they do not know the other income, they will just try to switch
            elif len(low_skilled_agents) > 0:
                for agent in low_skilled_agents:
                    self.model.agents_become_manual.append(agent)
            elif len(manual_other_agents) > 0:
                for agent in manual_other_agents:
                    self.model.agents_become_low_skilled_farm.append(agent)

            else:
                # Is there a non_labourer who maybe can help?
                for agent in self.household_members:
                    if agent.works == False:
                        if 11 <= agent.age <= 75:  # Assumption, 75 is the age you will definitly stop working
                            agent.works = True
                            self.model.agents_become_low_skilled_farm.append(
                                agent)

        # Do the young adults (15-35) want to migrate?
        possible_migrated_members = [
            agent for agent in self.household_members if agent.age > 15 and agent.age < 35]
        if len(possible_migrated_members) > 0:
            chance_migrating = self.model.chance_leaving_household
            if self.saw_advertisement == 1 and self.contacts_in_city == 1:
                chance_migrating += self.model.increased_chance_migration_familiarity # ASSUMPTION
            if self.random.random() < chance_migrating:  # They want to leave
                for agent in possible_migrated_members:
                    self.model.agents_become_migrated_members.append(agent)

        for agent in self.household_members:
            agent.income = 0


class Migrated_household(Agent):
    def __init__(self, model, agent_type, household_members):
        super().__init__(model)
        self.agent_type = agent_type
        self.household_members = household_members


class Migrated_hh_member(Agent):
    def __init__(self, model, agent_type, household):
        super().__init__(model)
        self.agent_type = agent_type
        self.household = household
