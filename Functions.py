import random
from mesa import Agent
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
    # When the number of children did not reach the max value, it is possible a child will be created
    if len([x for x in ages if x < 18]) < maximum_number_of_children:
        # To give birth to a child, the household members should be aged between 18 and 45
        if any(18 <= age <= 45 for age in ages): 
            #  A child is only born when there is a maximum age difference of 5 years old
            if min(ages) <= 5: 
                if np.random.rand() < birth_rate:
                    ages.append(0)

    # It is also possible that this is the first child 
    elif len([x for x in ages if x < 18]) == 0: 
        # When a parent is older than 45 it will not get a child anymore
        if min(ages) < 45: 
            if np.random.rand() < birth_rate:
                ages.append(0) 

    # Return the new ages
    ages.sort()
    return ages       

def education_levels(self): # Based on Tran et al., (2020)
    np.random.seed(20)
    education_levels = {"Primary":0.3, "Secondary":0.5, "Tertiary":0.6, "Higher education":0.7} # Based on nothing, basic education is useful but higher is less useful?
    probabilities = [0.475, 0.337, 0.158, 0.030] # Based on Tran et al., (2020)
    education_type = np.random.choice(list(education_levels.keys()), p=probabilities)
    education = education_levels[education_type]
    return education

def calculate_livelihood_agrifarm(meeting_agrocensus, education_level, farming_experience,community, government_support, savings, loans, land_size, measures, salinity):
    livelihood = {} 
    livelihood['human'] = np.average([meeting_agrocensus, education_level, farming_experience])
    livelihood['social'] = np.average([community, government_support])
    livelihood['financial'] = np.average([(max(0, min(savings / 10000, 1))), loans])
    livelihood['physical'] = np.average([(max(0, min(land_size / 2, 1))), (max(0, min(len(measures)*0.3, 1)))]) # Each measure increases the score by 0.3
    livelihood['natural'] = min(1, (1-salinity/12)) # maximum sainity = 12
    livelihood['average'] = np.average([livelihood['human'], livelihood['social'], livelihood['financial'], livelihood['physical'], livelihood['natural']])
    return livelihood

def calculate_cost(crop_type, seed_quality, land_size):
    if crop_type == "Triple_rice":
        if seed_quality == "Low":
            costs = 100 * land_size # UITZOEKEN, land_size in HA
        else:
            costs = 150 * land_size
    return costs

def calculate_yield(crop_type, salinity, land_size):
    if crop_type == 'Triple_rice':
        yield_per_ha = np.random.uniform(0.6, 0.8) # Average yield of rice is 0.6 or 0.8 ton/ha
        threshold = 3
        slope = 12
        current_salinity = salinity
        actual_yield = (100 - slope * (current_salinity - threshold)) * yield_per_ha * land_size # Based on Formula FAO
    return actual_yield

def calculate_income_farming(crop_type, seed_quality,  total_yield):
    if crop_type == "Triple_rice":
        prices = {"High":220, 'Low':205} # Price of rice in euros/ton, based on Tran et al, (2020)
        price = prices[seed_quality]
    yield_income = price * total_yield
    return yield_income 

def define_abilities(possible_strategies, strategies_requirements, savings, loan, human_livelihood, agro_meeting):
    abilities = []

    for strategy in strategies_requirements:
        if strategy['name'] in possible_strategies: # Check if strategy is possible

            # Financial Ability
            if savings >= strategy['price']:
                financial_ability = 1
            elif savings + loan >= strategy['price']:
                financial_ability = (savings+loan)/strategy['price']
            else:
                financial_ability = 0

            # Institutional Ability
            if human_livelihood >= strategy['knowledge']:
                institutional_ability = 1
            else:
                institutional_ability = max(0, human_livelihood / strategy['knowledge'])

            # Technical Ability
            if agro_meeting == 1:
                technical_ability = 1
            elif strategy['technical_ability'] == 0:
                technical_ability = 1
            else:
                technical_ability = 0

            # Average Ability
            avg_ability = (financial_ability + institutional_ability + technical_ability) / 3
            
            # Add results per strategy to a list
            abilities.append({
                "strategy": strategy['name'],
                "financial_ability": financial_ability,
                "institutional_ability": institutional_ability,
                "technical_ability": technical_ability,
                "average_ability": avg_ability
            })
    return abilities

def motivation__per_strategy(possible_strategies, strategies_requirements, livelihood_financial, livelihood_natural):
    motivations = {}
    for strategy in strategies_requirements:
        name = strategy['name']
        if name in possible_strategies: # Check if the strategy is possible or not for the farmer
            if strategy['type'] == "Water":
                if livelihood_natural < 0.3: # These numbers are based on nothing 
                    motivation = 1
                elif livelihood_natural > 0.7:
                    motivation = 0.1
                else:
                    motivation = 0.5
                motivations[name] = motivation
            elif strategy['type'] == "Crops":
                if livelihood_natural < 0.3:
                    motivation = 1
                elif livelihood_financial > 0.7:
                    motivation = 0
                else:
                    motivation = 0.5
                motivations[name] = motivation
    return motivations

def calculate_MOTA(motivations, abilities):
    MOTA_scores = {}
    for strategy in abilities:
        name = strategy['strategy']
        average_ability = strategy['average_ability']
        motivation = motivations[name]
        MOTA_scores[name] = average_ability * motivation
    return MOTA_scores

def find_best_strategy(MOTA_scores):
    highest_score = max(MOTA_scores.values()) # Check which strategy has the highest MOTA score 
    best_strategies = [name for name, score in MOTA_scores.items() if score == highest_score]
    best_strategy = np.random.choice(best_strategies) # If multiple strategies have the highest score, this will be random determined
    change = best_strategy if highest_score > 0.2 else None # If the highest MOTA score is below 0.2, the agent will change nothing (realistic value for 0.2 should be determined later!!)
    return change

def implement_strategy(change, savings, possible_strategies, requirements):
    # Delete change from possible strategies
    for strategy in requirements:
        if strategy["name"] == change:
            savings -= strategy["price"] # Pay for the strategy based on requirements
            possible_strategies.remove(change) # It is possible to only implement a strategy ones
            # technical abilities should increase, this should be implemented!!! 
    return possible_strategies, savings




    




            


