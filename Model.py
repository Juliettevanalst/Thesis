from mesa import Model, Agent
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
import networkx as nx
import random
import numpy as np

from Components import Agri_small_saline, Agri_small_fresh, Agri_middle_saline, Agri_middle_fresh, Agri_corporate_saline, Agri_corporate_fresh, Aqua_small

class Mekong_delta_model(Model):
    def __init__(self, seed=20, width = 15, height = 15, num_agents = {"Agri_small_saline": 0, "Agri_small_fresh": 0, "Agri_middle_saline":0, "Agri_middle_fresh": 0, "Agri_corporate_saline":0, "Agri_corporate_fresh": 0, "Aqua_small":20}):
        super().__init__(seed = seed)

        self.num_agents = num_agents
        self.grid = SingleGrid(width,height, torus=False) # Agents are for now put on a grid, with 4 neighbours

        self.seed = seed
        random.seed(20)
        np.random.seed(20)

        agent_classes = {"Agri_small_saline": Agri_small_saline, "Agri_small_fresh": Agri_small_fresh, "Agri_middle_saline": Agri_middle_saline,"Agri_middle_fresh": Agri_middle_fresh, "Agri_corporate_saline": Agri_corporate_saline, "Agri_corporate_fresh": Agri_corporate_fresh, "Aqua_small":Aqua_small}

        model_metrics = {}
        for name, cls in agent_classes.items():
            model_metrics[f"Income_{name}"] = (lambda m, cls = cls: np.mean([a.income for a in m.agents if isinstance(a, cls)]))
            model_metrics[f"Salinity_{name}"] = (lambda m, cls=cls: np.mean([a.salinity for a in m.agents if isinstance(a, cls)]))
            model_metrics[f"Savings_{name}"] = (lambda m, cls=cls: np.mean([a.savings for a in m.agents if isinstance(a, cls)]))
        agent_metrics = {"Cost_farming": "cost_farming","Cost_living": "cost_living","Income":"income", "Crop type":"crop_type", 
        "Savings":"savings", "Loan size":'loan_size', "Salinity":"salinity", "livelihood":"livelihood", "income_benefits": "income_benefits" ,"Ages":"ages", "MOTA scores": "MOTA_scores", "Change":"change", "Possible strategies" : lambda agent: agent.possible_strategies.copy()}
        self.datacollector = DataCollector(model_reporters = model_metrics, agent_reporters = agent_metrics)

        
        for agent_type, number_of_agents in self.num_agents.items():
            AgentClass = agent_classes[agent_type]

            for i in range(number_of_agents):
                agent = AgentClass(self, agent_type)
                self.agents.add(agent)

                while True:
                    x = self.random.randrange(self.grid.width)
                    y = self.random.randrange(self.grid.height)
                    if self.grid.is_cell_empty((x,y)):
                        break
                self.grid.place_agent(agent, (x,y)) # Distribute agents over the grid 

    def step(self):
        self.agents.shuffle_do('step') # Use random activation

        if self.steps % 12 == 0:
            self.datacollector.collect(self)
        
        