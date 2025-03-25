from mesa import Model, Agent
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
import networkx as nx
import random

from Components import Agri_small

class Mekong_delta_model(Model):
    def __init__(self, seed, width = 10, height = 10, num_agents = 20):
        super().__init__(seed = 20)

        self.num_agents = num_agents
        self.grid = SingleGrid(width,height, torus=False) # Agents are for now put on a grid, with 4 neighbours 

        model_metrics = {}
        agent_metrics = {"Cost_farming": "cost_farming","Cost_living": "cost_living","Income":"income", 
        "Savings":"savings", "Salinity":"salinity", "livelihood":"livelihood", "Ages":"ages"}
        self.datacollector = DataCollector(model_reporters = model_metrics, agent_reporters = agent_metrics)

        for i in range(self.num_agents):
            agent_type = "Agri_small"
            agent = Agri_small(self, agent_type)

            self.agents.add(agent)

            while True:
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                if self.grid.is_cell_empty((x,y)):
                    break
            self.grid.place_agent(agent, (x,y)) # Distribute agents over the grid

    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle_do('step') # Use random activation
        