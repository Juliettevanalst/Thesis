from mesa import Model, Agent
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
import networkx as nx
import random

from Components import Fragile_agri

class Mekong_delta_model(Model):
    def __init__(self, seed, width = 10, height = 10, num_agents = 20):
        super().__init__(seed = seed)

        self.num_agents = num_agents
        self.grid = SingleGrid(width,height, torus=False) # Agents are for now put on a grid, with 4 neighbours 

        model_metrics = {}
        agent_metrics = {"Income":"income", "Savings":"savings"}
        self.datacollector = DataCollector(model_reporters = model_metrics, agent_reporters = agent_metrics)

        for i in range(self.num_agents):
            agent_type = "Fragile_agri"
            agent = Fragile_agri(self, agent_type)

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
        