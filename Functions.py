import random
from mesa import Agent
import numpy as np

def create_household(max_number_children, max_number_grandparents):
    num_parents = 2
    parent_ages = [np.random.randint(20,50) for _ in range(num_parents)]
    num_grandparents = np.random.randint(2,max_number_grandparents)
    grandparent_ages = [np.random.randint(50,80) for _ in range(num_grandparents)]
    num_children = np.random.randint(0,max_number_children)
    child_ages = []
    if num_children > 0:
        first_child_age = np.random.randint(0,25)
        child_ages.append(first_child_age)
        for i in range(num_children-1):
            min_age = max(0, first_child_age - 5) # Max 5 year difference between children
            max_age = min(25, first_child_age + 5)
            new_child_age = np.random.randint(min_age, max_age + 1)
            child_ages.append(new_child_age)
    ages = child_ages + parent_ages + grandparent_ages
    return ages

def die(ages):
    survived_ages = []
    for age in ages:
        chance_death = min(1, max(0, (age - 80 + 10) / (2 * 10))) # Average death age = 80, std = 10 BASED ON NOTHING
        if np.random.rand() > chance_death:
            survived_ages.append(age) # These agents survive
    ages = survived_ages
    return ages

def education_levels(self): # Based on Tran et al., (2020)
    education_levels = {"Primary":0.3, "Secondary":0.5, "Tertiary":0.6, "Higher education":0.7} # Based on nothing, basic education is useful but higher is less useful?
    probabilities = [0.475, 0.337, 0.158, 0.030] # Based on Tran et al., (2020)
    education_type = np.random.choice(list(education_levels.keys()), p=probabilities)
    education = education_levels[education_type]
    return education

def calculate_livelihood_agrifarm(meeting_agrocensus, education_level, farming_experience,community, government_support, savings, loans, land_size, measures, salinity):
    livelihood_human = np.average([meeting_agrocensus, education_level, farming_experience])
    livelihood_social = np.average([community, government_support])
    livelihood_financial = np.average([(max(0, min(savings / 10000, 1))), loans])
    livelihood_physical = np.average([(max(0, min(land_size / 2, 1))), (max(0, min(len(measures)*0.3, 1)))]) # Each measure increases the score by 0.3
    livelihood_natural = min(1, (1-salinity/12)) # maximum sainity = 12
    livelihood = np.average([livelihood_human, livelihood_social, livelihood_financial, livelihood_physical, livelihood_natural])
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
        yield_per_ha = random.uniform(0.6, 0.8) # Average yield of rice is 0.6 or 0.8 ton/ha
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

def MOTA_framework(strategies, savings, loan, human_livelihood, agro_meeting):
    abilities = []

    for strategy in strategies:
        price, knowledge_needed, tech_needed = strategy['price'], strategy['knowledge'], strategy['technical_ability']

        # Financial Ability
        if savings >= price:
            financial_ability = 1
        elif savings + loan >= price:
            financial_ability = (savings+loan)/price
        else:
            financial_ability = 0

        # Institutional Ability
        if human_livelihood >= knowledge_needed:
            institutional_ability = 1
        else:
            institutional_ability = max(0, human_livelihood / knowledge_needed)

        # Technical Ability
        if agro_meeting == 1:
            technical_ability = 1
        elif tech_needed == 0:
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

    




            


