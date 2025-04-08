import random
from mesa import Agent, Model
import numpy as np

def create_household(max_number_children, max_number_grandparents):
    # Define number of parents. There are 2 parents, aged between 20 and 50, and their age difference is maximum 5 years
    num_parents = 2
    parent_ages = [random.randint(20,50)]
    mininum_age_2ndparent = max(20, parent_ages[0]- 5)
    maximum_age_2ndparent = min(45, parent_ages[0]+5)
    second_parent_age = random.randint(mininum_age_2ndparent, maximum_age_2ndparent + 1)
    parent_ages.append(second_parent_age)
    parent_ages.sort()

    # Define grandparents. They are between 50 and 80
    num_grandparents = np.random.randint(0,max_number_grandparents)
    grandparent_ages = [np.random.randint(50,80) for _ in range(num_grandparents)]

    # Define children. The first child should be minimal 16 years younger than the youngest parent. 
    # When there are already children, the age difference should be maximum of 5 years
    num_children = np.random.randint(0,max_number_children)
    child_ages = []
    if num_children > 0:
        minimum_age_1stchild = parent_ages[0] - 16
        first_child_age = np.random.randint(0,min(minimum_age_1stchild, 20))
        child_ages.append(first_child_age)

        for i in range(num_children - 1):
            minimum_age = max(0, first_child_age - 5)
            maximum_age = min(25, first_child_age - 1)
            if minimum_age < maximum_age:
                new_child_age = np.random.randint(minimum_age, maximum_age + 1)
                child_ages.append(new_child_age)
                first_child_age = new_child_age

    # Combine all ages together
    ages = child_ages + parent_ages + grandparent_ages
    return ages

def die(ages):
    # Each step, it is checked if an agent will die or not. The average death age = 80 with a std.dev of 10 years
    survived_ages = []
    for age in ages:
        chance_death = min(1, max(0, (age - 80 + 10) / (2 * 10))) # VALUES SHOULD BE DETERMINED LATER
        if np.random.rand() > chance_death:
            survived_ages.append(age) # These agents survive

    # Return all the agents that did not die, and sort them by age to make it easier
    ages = survived_ages
    ages.sort()
    return ages

def child_birth(ages, birth_rate, maximum_number_of_children):
    # If there are no children yet
    if len(ages) > 0:
        if min(ages) > 18: 
            # When a parent is older than 45 it will not get a child anymore
            if min(ages) < 45: 
                if np.random.rand() < birth_rate:
                    ages.append(0)
        
        # When the number of children did not reach the max value, it is possible a child will be created
        elif len([x for x in ages if x < 18]) < maximum_number_of_children:
            # To give birth to a child, the household members should be aged between 18 and 45
            if any(18 <= age <= 45 for age in ages): 
                #  A child is only born when there is a maximum age difference of 5 years old
                if min(ages) <= 5: 
                    if np.random.rand() < birth_rate:
                        ages.append(0)

    # Return the new ages
    ages.sort()
    return ages    

def education_levels(self): 
    # I gave every education level a random "level", this should be determined later, by for example doing sensitivity analysis
    education_levels = {"Primary":0.3, "Secondary":0.5, "Tertiary":0.6, "Higher education":0.7} # Based on nothing, basic education is useful but higher is less useful?
    probabilities = [0.475, 0.337, 0.158, 0.030] # Based on Tran et al., (2020)
    education_type = np.random.choice(list(education_levels.keys()), p=probabilities)
    education = education_levels[education_type]
    return education

def calculate_livelihood_agrifarm(meeting_agrocensus, education_level, salt_experience, government_support, savings, loans, maximal_debt, land_size, salinity):
    # Determine livelihoods based on sustainable livelihood approach
    livelihood = {} 
    livelihood['human'] = np.average([meeting_agrocensus, education_level, salt_experience])
    livelihood['social'] = np.average([government_support])
    livelihood['financial'] = np.average([(max(0, min(savings / 10000, 1))), loans/maximal_debt])
    livelihood['physical'] = np.average([(max(0, min(land_size / 2, 1)))]) 
    livelihood['natural'] = min(1, (1-salinity/12)) # maximum sainity = 12
    livelihood['average'] = np.average([livelihood['human'], livelihood['social'], livelihood['financial'], livelihood['physical'], livelihood['natural']])
    return livelihood

# I included this since Niels said this, but sepher said this is not happening --> Talk to Maaike tomorrow
# def salinity_influence_neighbours(model, node_id):
#     neighbors = model.G.neighbors(node_id)
#     salinities = [agent.salinity for n in neighbors for agent in model.grid.get_cell_list_contents([n]) if hasattr(agent, 'salinity')]
#     salinity = np.mean(salinities)
#     return salinity

def advice_agrocensus(salinity):
    # Based on certain salinity levels, agrocensus will advice you something. This is their calendar. 
    if salinity <= 3:
        adviced_crop = "Rice"
    elif salinity <= 5:
        adviced_crop = "Mango"
    elif salinity <= 9:
        adviced_crop = "Coconut"
    else:
        adviced_crop = "Shrimp"
    possible_next_crop = [adviced_crop]
    return possible_next_crop

def advice_neighbours(possible_next_crops, model,node_id):
    # Look at what your neighbors are doing, and add those to the possible crops you can do
    neighbors = model.G.neighbors(node_id)
    neighbor_crops = [neighbor_agent.current_crop for n in neighbors for neighbor_agent in model.grid.get_cell_list_contents([n]) if hasattr(neighbor_agent, 'current_crop')]
    possible_next_crops.extend(neighbor_crops)

    # Remove double crops
    possible_next_crops = list(set(possible_next_crops))
    return possible_next_crops

def define_abilities(possible_next_crops, savings, loan, maximum_loans, human_livelihood, salinity, water_level):
    abilities = []
    global requirements_per_crop
    requirements_per_crop = [{"name": "Rice", "switch_price": 1000, "knowledge": 0.7, "Water_level": 5, "salinity":3, "profit_over_five_years":9000}, 
    {"name": "Mango", "switch_price": 1500, "knowledge": 0.5, "Water_level": 4, "salinity":5, "profit_over_five_years":10000},
    {"name": "Coconut", "switch_price": 800, "knowledge": 0.6, "Water_level": 6, "salinity": 9, "profit_over_five_years":10000},
    {"name": "Shrimp", "switch_price": 1600, "knowledge": 0.6, "Water_level": 6, "salinity": 12, "profit_over_five_years":10000}] # THESE ARE ASSUMPTIONS AND CHANGE LATER BASED ON INTERVIEWS

    for crop in requirements_per_crop:
        if crop['name'] in possible_next_crops: # Check if crop change is possible, based on agrocensus meeting and neighbour

            # Financial Ability
            possible_debt_left = maximum_loans - loan
            if savings >= crop['switch_price']:
                financial_ability = 1
            elif savings + possible_debt_left >= crop['switch_price']:
                required_loan = crop['switch_price'] - savings
                # ASSUMPTION, PROFIT OVER FIVE YEAR SHOULD BE TWICE AS YOUR LOAN (since you also have other costs)
                if crop['profit_over_five_years'] / 2 > required_loan:
                    financial_ability = 0.5
                else:
                    financial_ability = 0
            else:
                financial_ability = 0

            # Institutional Ability
            if human_livelihood >= crop['knowledge']:
                institutional_ability = 1
            else:
                institutional_ability = max(0, human_livelihood / crop['knowledge'])

            # Technical Ability
            if salinity in range((crop['salinity']-2), (crop['salinity']+2)) and water_level in range((crop['salinity']-2), (crop['salinity']+2)):
                technical_ability = 1
            elif salinity in range((crop['salinity']-2), (crop['salinity']+2)) or water_level in range((crop['salinity']-2), (crop['salinity']+2)):
                technical_ability = 0.5
            else:
                technical_ability = 0
            
            # Average Ability
            if financial_ability == 0 or technical_ability == 0:
                avg_ability = 0
            else:        
                avg_ability = (financial_ability + institutional_ability + technical_ability) / 3
            
            # Add results per strategy to a list
            abilities.append({
                "strategy": crop['name'],
                "FA": financial_ability,
                "IA": institutional_ability,
                "TA": technical_ability,
                "average_ability": avg_ability
            })
    
    return abilities


def define_motivations(possible_next_crops, income, abilities):
    # Determine motivations per crop change
    motivations = {}
    for crop in requirements_per_crop:
        for ability in abilities:
            if ability['strategy'] == crop['name']:
                financial_ability = ability['FA']
                break
        if crop['name'] in possible_next_crops:
            # When the income of the crop is higher than your current income, you are motivated! If you also do not need a loan, you are more motivated 
            if crop['profit_over_five_years'] > income and financial_ability == 1: 
                motivation = 1
            elif crop['profit_over_five_years'] > income and financial_ability == 0.5: # You need a loan
                motivation = 0.5
            else:
                motivation = 0 # sensitivity analysis is required, since these numbers are based on my own imagination
            motivations[crop['name']] = motivation
   
    return motivations

def calculate_MOTA(motivations, abilities):
    
    MOTA_scores = {}
    # Calculate MOTA score, by multiplying ability by motivation 
    for ability in abilities:
        name = ability['strategy']
        average_ability = ability['average_ability']
        motivation = motivations[name]
        MOTA_scores[name] = average_ability * motivation
    
    return MOTA_scores

def best_MOTA(MOTA_scores, current_crop):
    highest_score = max(MOTA_scores.values()) # Check which strategy has the highest MOTA score 
    most_suitable_crop = [name for name, score in MOTA_scores.items() if score == highest_score]
    most_suitable_crop = np.random.choice(most_suitable_crop) # If multiple crops have the highest score, this will be random determined
    change = most_suitable_crop if highest_score > 0.2 else current_crop # If the highest MOTA score is below 0.2 (ASSUMPTION), the agent will change nothing (realistic value for 0.4 should be determined later!!)
    return change

def change_crops(change, savings, loan, maximum_loans):
    # Delete change from possible strategies
    for crop in requirements_per_crop:
        if crop["name"] == change:
            if crop['switch_price'] >= savings: # When the strategy is too expensive, the agent should implement loans
                loan += crop['switch_price'] - savings
                maximum_loans -= loan
                savings -= crop['switch_price'] + loan
            else:
                savings -= crop["switch_price"] # Pay for the strategy based on requirements
    return savings, loan, maximum_loans

def calculate_cost(crop_type, land_size):
    costs_per_crop = {"Rice": 100, "Mango":100, "Coconut":200} # THIS IS TOTALLYL RANDOM, will be based on interview later
    costs_per_ha = costs_per_crop[crop_type]
    costs = costs_per_ha * land_size
    return costs

def calculate_yield_agri(crop_type, salinity, land_size):
    if crop_type == 'Rice':
        yield_per_ha = np.random.uniform(0.6, 0.8) # Average yield of rice is 0.6 or 0.8 ton/ha
        threshold = 3
        slope = 12
    if crop_type == "Mango":
        yield_per_ha = np.random.uniform(12, 15)
        threshold = 5
        slope = 12
    elif crop_type == "Coconut":
        yield_per_ha = np.random.uniform(5, 7)
        threshold = 9
        slope = 15    # numbers are based on FAO
    
    current_salinity = salinity
    actual_yield = (((100 - slope * (current_salinity - threshold))/100) * yield_per_ha * land_size) # Based on Formula FAO
    return actual_yield

def calculate_income_farming(crop_type,  total_yield):
    if crop_type == "Rice":
        price = 400 # ASSUMPTION, this is price / ha
    elif crop_type == "Mango":
        price = 100
    elif crop_type == "Coconut":
        price = 200
    yield_income = price * total_yield
    return yield_income 

def calculate_farmers_spend_on_ww(income, number_of_ww, household_size):
    # this function calculates the amount of money farmers spend on wage workers. They will only spend money on wage workers when they earn enough themselves
    required_income = 1100 * household_size
    maximum_income_ww = 3000 * number_of_ww # There is also a maximum income the wage workers can get (ASSUMPTION)
    total_spend_ww = max(0, min((income - required_income), maximum_income_ww))
    return total_spend_ww

def calculate_migration_ww(income_too_low, contacts_in_city, facilities_in_neighbourhood):
    if income_too_low == 1 and contacts_in_city == 1 and facilities_in_neighbourhood < 0.5:
        chance = 1
    elif income_too_low == 1 and contacts_in_city == 1:
        chance = 0.8
    elif income_too_low ==1  and contacts_in_city == 0:
        chance = 0.5
    elif contacts_in_city == 1:
        chance = 0.15
    elif facilities_in_neighbourhood < 0.5:
        chance = 0.4
    else:
        chance = 0.1 # THESE ARE ALL RANDOM!!! DATA ANALYSIS IS REQUIRED 
    return chance

def decide_change_ww(income_per_agri_ww, income_per_aqua_ww, income, working_force, agent_type, ages):
    # These are the possibilities the wage worker agents have, when they want to change
    if agent_type == "Aqua":
        agri_income = income_per_agri_ww * working_force
        if agri_income > income:
            change = "Become_agri_ww"
            agent_type = "Agri"
        else:
            change = None
    elif agent_type == "Agri":
        aqua_income = income_per_aqua_ww * working_force
        if aqua_income > income:
            change = "Become_aqua_ww"
            agent_type = "Aqua"
        else:
            change = None

    child_who_can_work = 0
    # If it is not better to change to aqua/agri, you check if a child can work for you to earn more income
    if change == None:
        child_who_can_work = len([num for num in ages if 10 <= num <= 15])
        if child_who_can_work > 0:
            change = "increase_working_force"
            working_force += child_who_can_work
        
    return change, agent_type, working_force, child_who_can_work

        






            

    
