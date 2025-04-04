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

def education_levels(self): # Based on Tran et al., (2020)
    #np.random.seed(20)
    education_levels = {"Primary":0.3, "Secondary":0.5, "Tertiary":0.6, "Higher education":0.7} # Based on nothing, basic education is useful but higher is less useful?
    probabilities = [0.475, 0.337, 0.158, 0.030] # Based on Tran et al., (2020)
    education_type = np.random.choice(list(education_levels.keys()), p=probabilities)
    education = education_levels[education_type]
    return education

def calculate_livelihood_agrifarm(meeting_agrocensus, education_level, salt_experience,community, government_support, savings, loans, maximal_debt, land_size, equipment, salinity):
    livelihood = {} 
    livelihood['human'] = np.average([meeting_agrocensus, education_level, salt_experience])
    livelihood['social'] = np.average([community, government_support])
    livelihood['financial'] = np.average([(max(0, min(savings / 10000, 1))), loans/maximal_debt])
    livelihood['physical'] = np.average([(max(0, min(land_size / 2, 1))), (max(0, min(equipment, 1)))]) # Each measure increases the score by 0.3
    livelihood['natural'] = min(1, (1-salinity/12)) # maximum sainity = 12
    livelihood['average'] = np.average([livelihood['human'], livelihood['social'], livelihood['financial'], livelihood['physical'], livelihood['natural']])
    return livelihood

def calculate_cost(crop_or_fish_type, seed_or_feed_quality, land_size):
    if crop_or_fish_type == "Triple_rice":
        if seed_or_feed_quality == "Low":
            costs = 100 * land_size # UITZOEKEN, land_size in HA
        else:
            costs = 150 * land_size
    elif crop_or_fish_type == "Shrimp":
        if seed_or_feed_quality == "Low":
            costs = 100 * land_size
        else:
            costs = 150 * land_size
    return costs

def calculate_yield_agri(crop_type, salinity, land_size):
    if crop_type == 'Triple_rice':
        yield_per_ha = np.random.uniform(0.6, 0.8) # Average yield of rice is 0.6 or 0.8 ton/ha
        threshold = 3
        slope = 12
        current_salinity = salinity
        actual_yield = (((100 - slope * (current_salinity - threshold))/100) * yield_per_ha * land_size) # Based on Formula FAO
    return actual_yield

def calculate_yield_aqua(fish_type, farm_type, water_quality, disease, land_size):
    disease_intensity = 0.85 # ASSUMPTION, only 85% of the fish survives

    yield_per_ha = {"Extensive": {"Shrimp": 475}, "Intensive": {"Shrimp": 600}} # this is in kg, based on Joffre et al., 2015

    if farm_type in yield_per_ha:
        yield_aqua = yield_per_ha[farm_type][fish_type] * land_size * water_quality
    else:
        raise ValueError("Ongeldig farm_type opgegeven")

    if disease == 1:
        yield_aqua *= disease_intensity

    return yield_aqua
    

def calculate_income_farming(crop_type, seed_quality,  total_yield):
    if crop_type == "Triple_rice":
        prices_agri = {"High":500, 'Low':400} # Price of rice in euros/ton, based on Tran et al, (2020)
        price = prices_agri[seed_quality]
    yield_income = price * total_yield
    return yield_income 

def calculate_income_aqua(fish_type, farm_type, total_yield):
    if fish_type == "Shrimp":
        prices_aqua = {"Extensive":4, "Intensive":2} # Based on paper Joffre et al.,(2015)
        price = prices_aqua[farm_type]
    yield_income = price * total_yield
    return yield_income

def calculate_additional_income(meeting_agrocensus, income, land_size):
    average_support = 0.2 # BASED ON NOTHING
    boost = 0.4 if meeting_agrocensus == 1 else 0.0 # If you met agrocensus, the chance you get support from the government increases by 0.1
    chance_support = np.clip(np.random.normal(loc = average_support + boost, scale = 0.1), 0, 1)
    if np.random.rand() > chance_support: # if you get zero support:
        additional_income = 0
        support = 0
        return support, additional_income
    else:
        basis_income = land_size * 1200 # THIS IS RANDOM AND SHOULD BE DETERMIND LATER!!!!! 
        if income < basis_income:
            additional_income = basis_income - income 
            support = 1
            return support, additional_income 
        else:
            additional_income = 0
            support = 0
            return support, additional_income
                    

def calculate_benefits_government(ages):
    income_benefits = 0
    for age in ages:
        if age < 15:
            income_benefits += 50 # THIS IS TOTALLY RANDOM!!!!!
        elif age > 60:
            income_benefits += 50
    return income_benefits


def define_abilities(possible_strategies, strategies_requirements, savings, loan, maximum_loans, human_livelihood, equipment_level, number_of_facilities):
    abilities = []

    for strategy in strategies_requirements:
        if strategy['name'] in possible_strategies: # Check if strategy is possible

            # Financial Ability
            possible_debt_left = maximum_loans - loan
            if savings >= strategy['price']:
                financial_ability = 1
            elif savings + possible_debt_left >= strategy['price']:
                required_loan = strategy['price'] - savings
                if required_loan > savings:
                    financial_ability = 0.1
                else:
                    financial_ability = max(0, (required_loan/savings))
            else:
                financial_ability = 0

            # Institutional Ability
            if human_livelihood >= strategy['knowledge']:
                institutional_ability = 1
            else:
                institutional_ability = max(0, human_livelihood / strategy['knowledge'])

            # Technical Ability
            technical_ability = np.mean([equipment_level, number_of_facilities]) # NEED TO ADD NUMBER OF WAGE WORKERS AND WATER LEVEL!!

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
    change = best_strategy if highest_score > 0.4 else None # If the highest MOTA score is below 0.4, the agent will change nothing (realistic value for 0.4 should be determined later!!)
    return change

def implement_strategy(change, savings, possible_strategies, requirements, loan, maximum_loans):
    # Delete change from possible strategies
    for strategy in requirements:
        if strategy["name"] == change:
            if strategy['price'] >= savings: # When the strategy is too expensive, the agent should implement loans
                loan += strategy['price'] - savings
                maximum_loans -= loan
                savings -= strategy['price'] + loan
            else:
                savings -= strategy["price"] # Pay for the strategy based on requirements
            possible_strategies.remove(change) # It is possible to only implement a strategy ones
            # technical abilities should increase, this should be implemented!!! 
    return possible_strategies, savings, loan, maximum_loans




    




            


