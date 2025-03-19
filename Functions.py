import random
from mesa import Agent
import numpy as np

def yield_productivity(crop_type):
    regular_yield_productivities = {"High_quality_rice": 0.8, 'Low_quality_rice': 0.6} #DIT UITZOEKEN, ER STAAT NU 0.8 KG RIJST PER M2
    productivity = regular_yield_productivities[crop_type]
    return productivity

def calculate_income(crop_type, total_yield):
    prices = {"High_quality_rice":0.65, 'Low_quality_rice':0.50} # PRICE OF RICE IN EUROS DIT UITZOEKEN
    yield_income = prices[crop_type] * int(total_yield)
    return yield_income 