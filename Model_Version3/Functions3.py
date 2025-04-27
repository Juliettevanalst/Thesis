import random
from mesa import Agent, Model
import numpy as np
import statistics

def get_education_levels(age, model):
    if 0 <= age <= 15:
        group = (0, 15)
    elif 16 <= age <= 45:
        group = (16, 45)
    elif 46 <= age <= 59:
        group = (46, 59)
    elif 60 <= age <= 100:
        group = (59, 85)

    
    education_probability = model.excel_data['education_levels'][group]

    # Choose random level of education based on probabilities
    education_levels = list(education_probability.keys())
    probabilities = list(education_probability.values())
    chosen_education = random.choices(education_levels, weights = probabilities, k=1)[0]

    return chosen_education

def get_experience(occupation, model):
    experience_dict = model.excel_data['experience_occupation'][occupation]
    for key, values in experience_dict.items():
        if random.random() < experience_dict['Experience']:
            experience = 0
        else:
            experience = 1
        if random.random() < experience_dict['Machines']:
            machines = 0
        else:
            machines = 1
        experience_dict['Machines'] = machines
    return experience, machines

def get_dissabilities(age, model):
    if 0 <= age <= 15:
        group = (0, 15)
    elif 16 <= age <= 45:
        group = (16, 45)
    elif 46 <= age < 59:
        group = (46, 59)
    elif 59 <= age <= 100:
        group = (59, 85)

    dissability_dict = model.excel_data['dissabilities'][group]
    difficulties_list = []
    for function in ['Hearing', 'Seeing', 'Walking', 'Remembering']:
        difficulties = list(dissability_dict[function].keys())
        probabilities = list(dissability_dict[function].values())
        chosen_difficulty = random.choices(difficulties, weights = probabilities, k=1)[0]
        if chosen_difficulty == 'No_difficulty':
            difficulty = 0
        elif chosen_difficulty == "Some_difficulty":
            difficulty = 0.5
        elif chosen_difficulty == "Very_difficulty":
            difficulty = 0.75
        else:
            difficulty = 1
        difficulties_list.append(difficulty)
    
    if 1 in difficulties_list:
        return 1
    elif 0.75 in difficulties_list:
        return 0.75
    else:
        return statistics.mean(difficulties_list) 

def get_association(model, age):
    if age > 16: # I made the assumption you need to be an adult to be part of an association 
        chance_member = model.excel_data['association']     
        if random.random() < chance_member:
            return 1
    else:
        return 0 

def calculate_yield_agri(crop, land_area, salinity):
    # Dictionary layout = {"name":["threshold", "slope"]}
    salinity_decrease = {"Rice":[3,12], "Maize":[1.7, 12]}
    yield_per_ha = {"Rice":5753 , "Maize":4414, "Coconut":9871/6} # Based on FAO statistics ofo 2014. Shrimp is based on paper by Viet Khai et al., 2018
    if crop in salinity_decrease.keys():
        percentage_yield = ((100 - salinity_decrease[crop][1] * (salinity - salinity_decrease[crop][0]))/100) # Based on function FAO
    else:
        percentage_yield = 1 # Coconut is salt tolerant
    yield_ = yield_per_ha[crop] * land_area * percentage_yield
    return yield_

def calculate_farming_costs(crop, land_area):
    cost_per_ha = {"Rice":np.random.normal(16511894), "Maize":6800000, "Coconut":20000000/6} #All costs are per ha,
    costs = cost_per_ha[crop]

    total_cost = costs * land_area

    return total_cost

def calculate_yield_shrimp(land_area, disease, use_antibiotics):
    if disease == 1 and use_antibiotics == 0:
        yield_ = np.random.normal(37, 6.8) * land_area # this is in kg, based on paper joffre et al., 2015
    else:
        yield_ = np.random.normal(140, 20.9) * land_area

    return yield_

def calculate_cost_shrimp(land_size, use_antibiotics):
    costs = np.random.normal(3900000, 1000000) * land_size # based on joffre et al., (2015)
    if use_antibitics == 1:
        costs += 1000000 # Based on Viet Khai et al., (2018)

    return costs

def calculate_wages_farm_workers(crop, land_area, household_members, model):
    man_days_per_ha = {"Rice": 48, "Coconut":8, "Maize":106, "Shrimp":33} # Based on different papers, see documentation
    preparation_time = {"Rice": 14, "Coconut":45, "Maize":14, "Shrimp":14} # THIS IS AN ASSUMPTION, IN TWO WEEKS YOU WANT TO HAVE YOUR SEEDS PLANTED. for coconut the trees are already there, so prep time is long
    cultivation_time = {"Rice": 7, "Coconut": 2, "Maize": 14, "Shrimp": 14} # THESE ARE ASSUMPTIONS
    loan_per_day = 200000 # Based on paper by Pedroso et al., (2017)
    required_man_days = man_days_per_ha[crop] * land_area

    # THIS IS AN ASSUMPTION!! 1/3 OF PEOPLE IS NEEDED DURING SEED/PREPARATION TIME, 2/3 DURING CULTIVATION
    required_during_prep = required_man_days * model.man_days_prep
    required_during_cultivation = required_man_days * (1-model.man_days_prep)

    # Check how many people in the household are working on the farm
    cnt = 1
    for member in household_members:
        if member.agent_employment_type == "family_worker" and member.works == True:
            if member.agent_sector != "Non_agri":
                cnt += 1

    # Do we need to hire during preparation?
    required_during_prep_per_day = required_during_prep / preparation_time[crop]
    if cnt < required_during_prep_per_day:
        # You need to hire wage workers
        wage_workers = int((required_during_prep_per_day - cnt) * preparation_time[crop])
    else:
        wage_workers = 0

    # Do we need to hire during cultivation?
    required_during_cultivation_per_day = required_during_cultivation / cultivation_time[crop]
    if cnt < required_during_cultivation_per_day:
        # You need to hire wage workers
        wage_workers += int((required_during_cultivation_per_day - cnt) * cultivation_time[crop])
    else:
        wage_workers += 0

    cost_wage_workers = wage_workers * model.payment_low_skilled * model.distribution_high_low_skilled +  wage_workers * model.payment_high_skilled * (1-model.distribution_high_low_skilled)
    return cost_wage_workers, wage_workers

def calculate_total_income(crop, yield_, total_cost_farming):
    income_per_kg = {"Rice": 6049, "Coconut":17500, "Maize":6900, "Shrimp":42838} # Based on different papers, see documentation
    total_income = income_per_kg[crop] * yield_ - total_cost_farming
    return total_income

def calculate_livelihood(meeting, education, experience, dissability, social_situation, association, savings, debt, land_size, house_quality, salinity):
    livelihood = {}
    if savings > 0:
        savings_livelihood = 1
    else:
        savings_livelihood = 0

    livelihood['Human'] = np.average([meeting, education, experience, dissability])
    livelihood['Social'] = np.average([social_situation/100, association])
    livelihood['Financial'] = np.average([savings_livelihood, debt])
    livelihood['Physical'] = np.average([land_size, house_quality])
    livelihood['Natural'] = salinity

    livelihood['Average'] = np.average([livelihood['Human'], livelihood['Social'], livelihood['Financial'], livelihood['Physical'], livelihood['Natural']])
    return livelihood

def advice_agrocensus(salinity, education_level, current_crops):
    # Based on certain salinity levels, agrocensus will advice you something. This is their calendar. 
    if salinity <= 3 and "Rice" in current_crops:
        adviced_crop = "Rice"
    elif salinity <= 3 and "Maize" in current_crops:
        adviced_crop = "Maize"
    if education_level > 0.5: # THIS IS A RANDOM ASSUMPTION
        adviced_crop = "Shrimp"
    else:
        adviced_crop = "Coconut"
    possible_next_crop = [adviced_crop]
    return possible_next_crop

def advice_neighbours(possible_next_crops, model,node_id):
    # Look at what your neighbors are doing, and add those to the possible crops you can do
    neighbors = model.G.neighbors(node_id)
    neighbor_crops = []
    for n in neighbors:
        for neighbor_agent in model.grid.get_cell_list_contents([n]):
            if hasattr(neighbor_agent, 'crops_and_land'):
                crops = list(neighbor_agent.crops_and_land.keys())
                neighbor_crops.extend(crops)
    possible_next_crops.extend(neighbor_crops)
    possible_next_crops = [item for sublist in possible_next_crops for item in (sublist if isinstance(sublist, list) else [sublist])]


    possible_next_crops = list(set(possible_next_crops))  
    return possible_next_crops

def define_abilities(possible_next_crops, savings, loan, maximum_loans, human_livelihood, salinity, current_crop, land_size):
    abilities = []
    global requirements_per_crop
    requirements_per_crop = [{"name": "Rice", "switch_price": {"Maize":90000000, "Coconut":6751000, "Rice":0}, "knowledge": 0.5, "salinity":(0,6), "profit_over_five_years":3*34800000*5}, 
    {"name": "Maize", "switch_price": {"Maize":0, "Coconut":13833000, "Rice":43154500}, "knowledge": 0.5,  "salinity":(0,4), "profit_over_five_years":2*30450000*5},
    {"name": "Coconut", "switch_price": {"Maize":3931678, "Coconut":0, "Rice":52533000}, "knowledge": 0.5,  "salinity": (0,35), "profit_over_five_years":17500*12000*5},
    {"name": "Shrimp", "switch_price": {"Maize":50000000, "Coconut":333333000, "Rice":46365195}, "knowledge": 0.7, "salinity": (0,35), "profit_over_five_years":42838*140*2*5}] 

    for crop in requirements_per_crop:
        if crop['name'] in possible_next_crops: # Check if crop change is possible, based on agrocensus meeting and neighbour
            profit_over_five_years = crop['profit_over_five_years'] * land_size

            # If you switch to coconut, you will have half maize half coconut for the first 5 years, so your profit will be based on the maize
            if crop['name'] == "Coconut":
                profit_over_five_years = next(item["profit_over_five_years"] for item in requirements_per_crop if item["name"] == "Maize") * 0.5 * land_size 

            # Financial Ability
            possible_debt_left = maximum_loans - loan
            if current_crop == crop['name']:
                # You already have the crop! Therefore, there won't be a switching price
                financial_ability = 1
            else:
                # You do need to pay the switching price
                if savings >= crop['switch_price'][current_crop] * land_size:
                    financial_ability = 1
                elif savings + possible_debt_left >= crop['switch_price'][current_crop] * land_size:
                    required_loan = crop['switch_price'][current_crop] * land_size - savings
                    # ASSUMPTION, PROFIT OVER FIVE YEAR SHOULD BE TWICE AS YOUR LOAN (since you also have other costs)
                    if profit_over_five_years / 2 > required_loan:
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
            if crop['salinity'][0] <= salinity < crop['salinity'][1]:
                technical_ability = 1
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

    # for ability in abilities:
    #     print(ability['average_ability'])
    return abilities

def define_motivations(possible_next_crops, yearly_income, abilities, current_crop, required_income, land_size):
    # Determine motivations per crop change
    motivations = {}
    for crop in requirements_per_crop:
        for ability in abilities:
            if ability['strategy'] == crop['name']:
                financial_ability = ability['FA']
                break
        if crop['name'] in possible_next_crops:
            if crop['name'] != current_crop:
                # The same as by abilities, if you have coconut your profit will be defined on half maize
                if crop['name'] == "Coconut":
                    profit_over_five_years = next(item["profit_over_five_years"] for item in requirements_per_crop if item["name"] == "Maize") * 0.5 * land_size
                else:
                    profit_over_five_years = crop['profit_over_five_years']
                
                # When the income of the crop is higher than your current income, you are motivated! If you also do not need a loan, you are more motivated 
                if profit_over_five_years*land_size/5 > yearly_income and financial_ability == 1: 
                    motivation = 1
                elif profit_over_five_years*land_size/5 > yearly_income and financial_ability == 0.5: # You need a loan
                    motivation = 0.5
                else:
                    motivation = 0 # sensitivity analysis is required, since these numbers are based on my own imagination
            else:
                if yearly_income > required_income:
                    motivation = 1
                else:
                    motivation = 0.2 # ASSUMPTION,  you already have the knowledge so you are little motivated
            motivations[crop['name']] = motivation
            # print("motivation voor ", crop['name'], " is ", motivation)   
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
    # if change != current_crop:
        # print("we gaan veranderen naar... ", change)
    return change

def change_crops(change, savings, loan, maximum_loans, land_size, current_crop):
    # Delete change from possible strategies
    for crop in requirements_per_crop:
        if crop["name"] == change:
            if crop['switch_price'][current_crop]*land_size >= savings: # When the strategy is too expensive, the agent should implement loans
                loan += (crop['switch_price'][current_crop]*land_size  - savings)
                maximum_loans -= loan
                savings = 0
            else:
                savings -= crop["switch_price"][current_crop]*land_size  # Pay for the strategy based on requirements
    if change != 'Coconut':
        crops_and_land = {crop['name']:land_size}
        waiting_time = 0
    else:
        crops_and_land = {'Coconut':land_size/2, 'Maize': land_size/2}
        waiting_time = 60 # You need to wait 5 years untill you can start with your coconut
    return savings, loan, maximum_loans, crops_and_land, waiting_time

def annual_loan_payment(loan_size, interest_rate_loans):
    annual_loan = loan_size * (interest_rate_loans * (1+ interest_rate_loans)**5) / ((1+interest_rate_loans)**5 - 1) # This is based on annuïteitenberekenings
    return annual_loan
    


