from mesa import Agent
import numpy as np
import random

class Agri_farmer(Agent):
    def __init__(self, model, agent_type, node_id):
        super().__init__(model)
        self.agent_type = agent_type
        self.node_id = node_id
        
    def step(self):
       pass

class Agri_small_saline(Agri_farmer):
    def __init__(self, model, agent_type, node_id):
        super().__init__(model, "Agri_small_saline", node_id)  
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)

    def step(self):
        pass

class Agri_small_fresh(Agri_farmer):
    def __init__(self, model, agent_type, node_id):
        super().__init__(model, "Agri_small_fresh", node_id)
        agent_seed = self.model.random.randint(0,1000)
        np.random.seed(agent_seed)

    def step(self):
        pass