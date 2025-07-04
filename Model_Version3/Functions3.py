import random
from mesa import Agent, Model
import numpy as np
import statistics


def get_education_levels(age, model):
    """Function to give an agent an education level, based on their age.

    1. the age group is determined
    2. The probabilities for each type of education are checked, using excel data and the age group
    3. A random choice is made, with the probabilities as weights

    """
    if 0 <= age <= 15:
        group = (0, 15)
    elif 16 <= age <= 45:
        group = (16, 45)
    elif 46 <= age <= 59:
        group = (46, 59)
    elif 60 <= age <= 500:
        group = (59, 85)

    education_probability = model.excel_data['education_levels'][group]

    # Choose random level of education based on probabilities
    education_levels = list(education_probability.keys())
    probabilities = list(education_probability.values())
    chosen_education = random.choices(
        education_levels, weights=probabilities, k=1)[0]

    return chosen_education


def get_experience(occupation, model):
    """
    For the individual agents, it is checked if they have 3+ years experience and if they  use machines
    This is based on their occupation, and the excel file
    """
    experience_dict = model.excel_data['experience_occupation'][occupation]
    for key, values in experience_dict.items():
        if model.machines_experiment != 2:
            probability_machine = model.machines_experiment
        else:
            probability_machine = experience_dict['Machines']

        if random.random() < experience_dict['Experience']:
            experience = 0
        else:
            experience = 1
        # experience_dict['Machines']:
        if random.random() < probability_machine:
            machines = 0
        else:
            machines = 1

        experience_dict['Machines'] = machines
    return experience, machines


def household_experience_machines(household_members):
    """
    For all land households, the average experience levels are checked
    Furthermore, it is checked if someone in the family is familiar with machines, then machines == 1

    """
    experience_levels = []
    machines = 0
    for agent in household_members:
        if agent.age > 15:
            experience_levels.append(agent.experience)
            if agent.machines == 1:
                machines = 1
    if len(experience_levels) == 0:
        experience_levels = [0]  # DE DEATH RATE STAAT TE HOOG
    average_experience = statistics.mean(experience_levels)
    return machines, average_experience


def get_dissabilities(age, model):
    """
    For all household members, an average dissability level is determined
    This is based on data in the excel file

    If someone has "very_difficulty" with something, its dissabilities level is0.75
    If someone is unable to do something, its dissabilities level is 1.
    Otherewise, its dissabilities level is equal to the average of their dissabilities
    """
    if 0 <= age <= 15:
        group = (0, 15)
    elif 16 <= age <= 45:
        group = (16, 45)
    elif 46 <= age < 59:
        group = (46, 59)
    elif 59 <= age <= 500:
        group = (59, 85)

    dissability_dict = model.excel_data['dissabilities'][group]
    difficulties_list = []
    for function in ['Hearing', 'Seeing', 'Walking', 'Remembering']:
        difficulties = list(dissability_dict[function].keys())
        probabilities = list(dissability_dict[function].values())
        chosen_difficulty = random.choices(
            difficulties, weights=probabilities, k=1)[0]
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


def get_association(model):
    """
    This function determines, based on the excel data,
    if a land household is member of the association or not
    """
    chance_member = model.excel_data['association']
    if random.random() < chance_member:
        return 1
    else:
        return 0


def calculate_yield_agri(
        crop,
        land_area,
        salinity,
        human_livelihood,
        percentage_yield_):
    """
    Function to calculate the yield in agriculture.
    First, it is checked what the yield reduction is due to salinity, while using the FAO formula.
        (Only rice and Maize are impacted by salinity)
    The total yield is calculated, based on yield per ha, multiplied by land size and the yield reduction of salinity
    When the household is smarter, the household is less impacted by salinity. This is based on the human_livelihood

    """
    # Dictionary layout = {"name":["threshold", "slope"]}
    salinity_decrease = {"Rice": [3, 12], "Maize": [1.7, 12]}
    # Based on FAO statistics of 2014
    yield_per_ha = {"Rice": 5753, "Maize": 4414, "Coconut": 9871 / 6}
    if crop in salinity_decrease.keys():
        percentage_yield_[crop] = ((100 -
                                    salinity_decrease[crop][1] *
                                    (salinity -
                                        salinity_decrease[crop][0])) /
                                   100)  # Based on function FAO
        # yield will always be maximum 1, also if your salinity is below the
        # threshold.
        percentage_yield_[crop] = min(percentage_yield_[crop], 1)
    else:
        percentage_yield_[crop] = 1  # Coconut is salt tolerant

    # When you are smarter, yield will be less impacted by salinity:
    if human_livelihood >= 0.5:  # THIS VALUE IS AN ASSUMPTION!!
        percentage_yield_[crop] = min(percentage_yield_[crop] + 0.1, 1)

    yield_ = yield_per_ha[crop] * land_area * percentage_yield_[crop]

    return yield_, percentage_yield_[crop]


def calculate_farming_costs(crop, land_area, model):
    """
    Function to calculate the farming costs of a certain crop
    The costs are based on fixed costs per ha, and the land size for the crop on the farm
    """

    # All costs are per ha,  DEZE WAREN EERST GEDEELD DOOR 6, MAAR DAT WERD
    # ERG LUXE.
    cost_per_ha = {
        "Rice": model.fixed_costs_rice,
        "Maize": model.fixed_costs_maize,
        "Coconut": model.fixed_costs_coconut}
    costs = cost_per_ha[crop]

    total_cost = costs * land_area

    return total_cost


def calculate_yield_shrimp(land_area, disease, use_antibiotics):
    """Function to calculate the shrimp yield.

    If a disease happened, and no antibiotics are used, the shrimp yield will be less
    The yield is multiplied by land size for shrimp per farm
    """
    if disease == 1 and use_antibiotics == 0:
        # this is in kg, based on paper joffre et al., 2015
        yield_ = 37 * land_area
    else:
        yield_ = 140 * land_area

    return yield_


def calculate_cost_shrimp(land_size, use_antibiotics, model):
    """
    Function to calculate the costs of shrimp

    When antibiotics is used, they need to pay extra
    The costs are per ha, and need to be multiplied by the land size
    """
    # based on joffre et al., (2015)
    costs = model.fixed_costs_shrimp * land_size
    if use_antibiotics == 1:
        costs += 1000000 * land_size  # Based on Viet Khai et al., (2018)

    return costs


def calculate_wages_farm_workers(
        crop,
        land_area,
        household_members,
        model,
        machines,
        percentage_yield):
    """Function to calculate the wage costs of agri wage workers, per farm household
    This is calculated in a few steps:
    1. determine the  man days/ha of the crop
    2. calculate the required man days, based on your land area
    3. Check if you have machines, then you need less wage workers during cultivation
    4. Check how many of the household members are working on the farm
    5. Calculate if we need to hire during preparation and cultivation time
    6. Determine the costs of the wage workers, based on the distribution of high and low skilled workers
    """
    # Based on different papers, see documentation
    man_days_per_ha = {"Rice": 48, "Coconut": 8, "Maize": 106, "Shrimp": 33}
    # THIS IS AN ASSUMPTION, IN TWO WEEKS YOU WANT TO HAVE YOUR SEEDS PLANTED.
    # for coconut the trees are already there, so prep time is long
    preparation_time = {"Rice": 14, "Coconut": 45, "Maize": 14, "Shrimp": 14}
    cultivation_time = {"Rice": 7, "Coconut": 2,
                        "Maize": 14, "Shrimp": 14}  # THESE ARE ASSUMPTIONS
    loan_per_day = 200000  # Based on paper by Pedroso et al., (2017)
    required_man_days = man_days_per_ha[crop] * land_area

    # If you have machines and experience as a farm, you will only need 1/3 of
    # the people during cultivation
    if machines == 1:
        required_during_prep = required_man_days * model.man_days_prep
        required_during_cultivation = required_man_days * \
            (1 - model.man_days_prep) / 2
    # Otherwise, you will need 1/3 of the people during preparation and 2/3 of
    # the people during cultivation
    else:
        required_during_prep = required_man_days * model.man_days_prep
        required_during_cultivation = required_man_days * \
            (1 - model.man_days_prep)

    # Check how many people in the household are working on the farm
    cnt = 1
    for member in household_members:
        if member.agent_employment_type == "family_worker" and member.works:
            if member.agent_sector != "Non_agri":
                cnt += 1

    # Do we need to hire during preparation?
    required_during_prep_per_day = required_during_prep / \
        preparation_time[crop]
    if cnt < required_during_prep_per_day:
        # You need to hire wage workers
        wage_workers = int((required_during_prep_per_day - cnt)
                           * preparation_time[crop])
    else:
        wage_workers = 0

    # Do we need to hire during cultivation?
    required_during_cultivation_per_day = required_during_cultivation / \
        cultivation_time[crop]
    # Also take the yield reduction due to salinity into account. If the yield
    # was less, the number of wage workers is decreased.
    if cnt < required_during_cultivation_per_day:
        # You need to hire wage workers
        wage_workers += int((required_during_cultivation_per_day - cnt)
                            * cultivation_time[crop] * percentage_yield)
    else:
        wage_workers += 0

    cost_wage_workers = wage_workers * model.payment_low_skilled * model.distribution_high_low_skilled + \
        wage_workers * model.payment_high_skilled * (1 - model.distribution_high_low_skilled)

    return cost_wage_workers, wage_workers


def calculate_total_income(crop, yield_, total_cost_farming):
    """Calculate total income per crop, based on income in vnd per kg and crop yield, minus total costs of farming"""
    # Based on different papers, see documentation
    income_per_kg = {"Rice": 6049, "Coconut": 17500,
                     "Maize": 6900, "Shrimp": 42838 * 9}
    total_income = income_per_kg[crop] * yield_ - total_cost_farming
    return total_income


def calculate_livelihood(
        meeting,
        education,
        experience,
        dissability,
        social_situation,
        association,
        savings,
        debt,
        land_size,
        house_quality,
        salinity):
    """
    Function to calculate the livelihoods of households.

    There are five livelihood factors: human, social, financial, physical, natural

    For each livelihood factor, the average is taken of the variables
    Average livelihood is calculated by taking the average of all livelihood factors
    """
    livelihood = {}
    if savings > 0:
        savings_livelihood = 1
    else:
        savings_livelihood = 0

    livelihood['Human'] = np.average(
        [meeting, education, experience, dissability])
    livelihood['Social'] = np.average([social_situation, association])
    livelihood['Financial'] = np.average([savings_livelihood, (1 - debt)])
    livelihood['Physical'] = np.average([land_size, house_quality])
    livelihood['Natural'] = salinity

    # Calculate the average livelihood
    livelihood['Average'] = np.average(
        [
            livelihood['Human'],
            livelihood['Social'],
            livelihood['Financial'],
            livelihood['Physical'],
            livelihood['Natural']])
    return livelihood


def advice_agrocensus(salinity, education_level, current_crops):
    """
    If your household went to the information meeting, you will get an adviced crop
    This avice is based on your salinity levels.
    """
    # Based on certain salinity levels, agrocensus will advice you something.
    # This is their calendar.
    if salinity <= 3 and "Rice" in current_crops:
        adviced_crop = "Rice"
    elif salinity <= 3 and "Maize" in current_crops:
        adviced_crop = "Maize"
    elif education_level > 0.5:
        adviced_crop = "Shrimp"
    else:
        adviced_crop = "Coconut"
    possible_next_crop = [adviced_crop]
    return possible_next_crop


def advice_neighbours(possible_next_crops, model, node_id):
    """
    Function for land households to check what their neighbors are cultivating.
    These crops are taken into account as possible next crops
    """
    # Look at what your neighbors are doing, and add those to the possible
    # crops you can do
    neighbors = model.G.neighbors(node_id)
    neighbor_crops = []
    for n in neighbors:
        for neighbor_agent in model.grid.get_cell_list_contents([n]):
            if hasattr(neighbor_agent, 'crops_and_land'):
                crops = list(neighbor_agent.crops_and_land.keys())
                neighbor_crops.extend(crops)
    possible_next_crops.extend(neighbor_crops)
    possible_next_crops = [
        item for sublist in possible_next_crops for item in (
            sublist if isinstance(
                sublist, list) else [sublist])]

    possible_next_crops = list(set(possible_next_crops))
    return possible_next_crops


def define_abilities(
        possible_next_crops,
        savings,
        loan,
        maximum_loans,
        human_livelihood,
        salinity,
        current_crop,
        land_size,
        machines):
    """
    To determine the best next crop, MOTA framework is used.
    This function determines the ability scores for each possible next crop
    Technical ability, institutional ability and financial ability are calculated
    Average ability will be zero when your technical ability or financial ability are 0
    """
    abilities = []
    global requirements_per_crop
    requirements_per_crop = [{"name": "Rice",
                              "switch_price": {"Maize": 90000000,
                                               "Coconut": 6751000,
                                               "Rice": 0},
                              "knowledge": 0.5,
                              "salinity": (0,
                                           6),
                              "profit_over_five_years": 3 * 34800000 * 5},
                             {"name": "Maize",
                              "switch_price": {"Maize": 0,
                                               "Coconut": 13833000,
                                               "Rice": 43154500},
                              "knowledge": 0.5,
                              "salinity": (0,
                                           4),
                              "profit_over_five_years": 2 * 30450000 * 5},
                             {"name": "Coconut",
                              "switch_price": {"Maize": 3931678,
                                               "Coconut": 0,
                                               "Rice": 52533000},
                              "knowledge": 0.5,
                              "salinity": (0,
                                           35),
                              "profit_over_five_years": 17500 * 12000 * 5},
                             {"name": "Shrimp",
                              "switch_price": {"Maize": 50000000,
                                               "Coconut": 333333000,
                                               "Rice": 46365195},
                              "knowledge": 0.7,
                              "salinity": (0,
                                           35),
                              "profit_over_five_years": 42838 * 140 * 2 * 5}]

    for crop in requirements_per_crop:
        # Check if crop change is possible, based on agrocensus meeting and
        # neighbour
        if crop['name'] in possible_next_crops:
            profit_over_five_years = crop['profit_over_five_years'] * land_size

            # If you switch to coconut, you will have half maize/rice half
            # coconut for the first 5 years, so your profit will be based on
            # the maize or rice
            if crop['name'] == "Coconut":
                if current_crop == "Maize":
                    profit_over_five_years = next(
                        item["profit_over_five_years"] for item in requirements_per_crop if item["name"] == "Maize") * 0.5 * land_size
                elif current_crop == "Rice":
                    profit_over_five_years = next(
                        item["profit_over_five_years"] for item in requirements_per_crop if item["name"] == "Rice") * 0.5 * land_size

            # Financial Ability
            possible_debt_left = maximum_loans
            if current_crop == crop['name']:
                # You already have the crop! Therefore, there won't be a
                # switching price
                financial_ability = 1
            else:
                # You do need to pay the switching price
                if savings >= crop['switch_price'][current_crop] * land_size:
                    financial_ability = 1
                elif savings + possible_debt_left >= crop['switch_price'][current_crop] * land_size:
                    required_loan = crop['switch_price'][current_crop] * \
                        land_size - savings
                    # ASSUMPTION, PROFIT OVER FIVE YEAR SHOULD BE TWICE AS YOUR
                    # LOAN (since you also have other costs)
                    if profit_over_five_years / 2 > required_loan and required_loan < possible_debt_left:
                        financial_ability = 0.5
                    else:
                        financial_ability = 0
                else:
                    financial_ability = 0

            # Institutional Ability
            if human_livelihood >= crop['knowledge']:
                institutional_ability = 1
            else:
                institutional_ability = max(
                    0, human_livelihood / crop['knowledge'])

            # Technical Ability
            technical_ability = 0
            if crop['salinity'][0] <= salinity < crop['salinity'][1]:
                if crop['name'] == "Maize":
                    # Based on current liturature data, your production costs
                    # will be too high if the land size is higher than 1 and
                    # you do not have machines.
                    if land_size < 1 or machines == 1:
                        technical_ability = 1
                elif crop['name'] == "Coconut" and current_crop == "Maize":
                    if land_size / 2 < 1 or machines == 1:
                        technical_ability = 1
                else:
                    technical_ability = 1

            # Average Ability
            if financial_ability == 0 or technical_ability == 0:
                avg_ability = 0
            else:
                avg_ability = (financial_ability +
                               institutional_ability + technical_ability) / 3

            # Add results per strategy to a list
            abilities.append({
                "strategy": crop['name'],
                "FA": financial_ability,
                "IA": institutional_ability,
                "TA": technical_ability,
                "average_ability": avg_ability
            })

    return abilities


def define_motivations(
        possible_next_crops,
        yearly_income,
        abilities,
        current_crop,
        required_income,
        land_size):
    """
    To determine the best next crop, MOTA framework is used.
    This function determines the motivation for each possible next crop
    Motivation is based on financial ability,
        and if the profit over five years is higher than the current profit of the household
    """

    # Determine motivations per crop change
    motivations = {}
    for crop in requirements_per_crop:
        for ability in abilities:
            if ability['strategy'] == crop['name']:
                financial_ability = ability['FA']
                break
        if crop['name'] in possible_next_crops:
            if crop['name'] != current_crop:
                # The same as by abilities, if you have coconut your profit
                # will be defined on half maize
                if crop['name'] == "Coconut":
                    if current_crop == "Maize":
                        profit_over_five_years = next(
                            item["profit_over_five_years"] for item in requirements_per_crop if item["name"] == "Maize") * 0.5 * land_size
                    elif current_crop == "Rice":
                        profit_over_five_years = next(
                            item["profit_over_five_years"] for item in requirements_per_crop if item["name"] == "Rice") * 0.5 * land_size

                else:
                    profit_over_five_years = crop['profit_over_five_years']

                # When the income of the crop is higher than your current
                # income, you are motivated! If you also do not need a loan,
                # you are more motivated
                if profit_over_five_years * land_size / \
                        5 > yearly_income and financial_ability == 1:
                    motivation = 1
                elif profit_over_five_years * land_size / 5 > yearly_income and financial_ability == 0.5:  # You need a loan
                    motivation = 0.5
                else:
                    motivation = 0  # sensitivity analysis is required, since these numbers are based on my own imagination
            else:
                if yearly_income > required_income:
                    motivation = 1
                else:
                    motivation = 0.2  # ASSUMPTION,  you already have the knowledge so you are little motivated
            motivations[crop['name']] = motivation
            # print("motivation voor ", crop['name'], " is ", motivation)

    return motivations


def calculate_MOTA(motivations, abilities):
    """
    Function to calculate the MOTA scores for each possible next crop
    The scores are calculated by multiplying the ability by the motivation per crop
    """

    MOTA_scores = {}
    # Calculate MOTA score, by multiplying ability by motivation
    for ability in abilities:
        name = ability['strategy']
        average_ability = ability['average_ability']
        motivation = motivations[name]
        MOTA_scores[name] = average_ability * motivation

    return MOTA_scores


def best_MOTA(MOTA_scores, current_crop):
    """
    Function to check which possible next crop has the highest MOTA score
    """
    # Check which strategy has the highest MOTA score
    highest_score = max(MOTA_scores.values())
    most_suitable_crop = [
        name for name,
        score in MOTA_scores.items() if score == highest_score]
    # If multiple crops have the highest score, this will be random determined
    if len(most_suitable_crop) > 1 and current_crop in most_suitable_crop:
        most_suitable_crop.remove(current_crop)
    most_suitable_crop = np.random.choice(most_suitable_crop)
    # If the highest MOTA score is below 0.2 (ASSUMPTION), the agent will
    # change nothing
    change = most_suitable_crop if highest_score > 0.2 else None
    return change


def change_crops(
        change,
        savings,
        loan,
        maximum_loans,
        land_size,
        current_largest_crop,
        current_crop,
        waiting_time_):
    """
    When the next crop of a land household is not the same as the current crop,
    the household needs to implement changes,

    This function checks if a loan is required for the land change, and decreases savings,
    Furthermore, it checks if a waiting time is required and changes the crops_and_land dictionary
    """
    sector_crop_dict = {
        'Annual crops': 'Maize',
        "Aquaculture": "Shrimp",
        "Perennial crops": "Coconut",
        "Rice": "Rice"}
    new_crop_type = None
    # Delete change from possible strategies
    for crop in requirements_per_crop:
        if crop["name"] == change:
            # When the strategy is too expensive, the agent should implement
            # loans
            if crop['switch_price'][current_largest_crop] * \
                    land_size >= savings:
                loan += (crop['switch_price'][current_largest_crop]
                         * land_size - savings)
                maximum_loans -= loan
                savings = 0
            else:
                # Pay for the strategy based on requirements
                savings -= crop["switch_price"][current_largest_crop] * land_size

            # Define new sector for the agent
            for crop_type, crop_itself in sector_crop_dict.items():
                if crop_itself == crop['name']:
                    new_crop_type = crop_type
    if change != 'Coconut':
        crops_and_land = {change: land_size}
        # You can not harvest rice in february and harvest a complete shrimp
        # field in april
        waiting_time_[change] = 6
    else:
        if "Rice" in current_crop:
            crops_and_land = {'Coconut': land_size, 'Rice': (land_size / 2)}
        elif "Maize" in current_crop:
            crops_and_land = {'Coconut': land_size, 'Maize': (land_size / 2)}
        # You need to wait 5 years untill you can start with your coconut
        waiting_time_[change] = 60
    return savings, loan, maximum_loans, crops_and_land, waiting_time_, new_crop_type


def transfer_land(land_size, node_id, model, crops_and_land):
    """
    When a land household is migrating, there is a possibility for neighbors to buy the land
    This possibility and transfer is checked in this function.

    First the best neighbor is determined based on financial livelihoods.
    Second, it is checked if the neighbor can pay for the land or not.
        If this is the case, the land is added to the neighbors land
    """
    from Agents3 import Small_land_households, Middle_land_households, Large_land_households
    # Define neighbors
    neighbors = model.G.neighbors(node_id)
    max_livelihood = 0
    best_neighbor = None

    for neighbor in neighbors:
        agents = model.grid.get_cell_list_contents([neighbor])
    # agents is a list, so we need to take the first item of the list
    if agents:
        agent = agents[0]
        if agent.livelihood['Financial'] > max_livelihood:
            max_livelihood = agent.livelihood['Financial']
            best_neighbor = agent

        if best_neighbor:
            # Check if the best neighbor can pay for the land
            land_costs = land_size * model.land_price_per_ha
            if best_neighbor.savings > land_costs:
                best_neighbor.land_area += land_size
                best_neighbor.savings -= land_costs

                # Check in which category the agent now falls
                if 0 <= best_neighbor.land_area <= 0.5:
                    best_neighbor.land_category = "small"
                elif 0.5 < best_neighbor.land_area <= 2:
                    best_neighbor.land_category = "medium"
                else:
                    best_neighbor.land_category = "large"

                # Add this to the crops_and_land
                for crop, area in crops_and_land.items():
                    if crop in best_neighbor.crops_and_land:
                        best_neighbor.crops_and_land[crop] += area
                    else:
                        best_neighbor.crops_and_land[crop] = area


def annual_loan_payment(loan_size, interest_rate_loans):
    """
    When a household has a loan, it needs to pay this back in 5 years.
    There is also an interest rate on the loan

    To calculte the yearly payment, taking the interest rate into account, the annuity calculation is used
    """
    annual_loan = loan_size * (interest_rate_loans * (1 + interest_rate_loans)**5) / (
        (1 + interest_rate_loans)**5 - 1)
    return annual_loan


def calculate_migration_ww(
        model,
        income_too_low,
        contacts_in_city,
        facilities_in_neighbourhood):
    """
    There is a possibility that the landless households are migrating.
    This function determines how big this chance is.
    """
    chances = model.chances_migration
    if income_too_low == 1 and contacts_in_city == 1 and facilities_in_neighbourhood < 0.5:
        chance = chances[0]
    elif income_too_low == 1 and contacts_in_city == 1:
        chance = chances[1]
    elif income_too_low == 1 and contacts_in_city == 0:
        chance = chances[2]
    elif contacts_in_city == 1:
        chance = chances[3]
    elif facilities_in_neighbourhood < 0.5:
        chance = chances[4]
    else:
        chance = chances[5]
    return chance
