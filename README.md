Created by Juliëtte van Alst

Hoi Alexander, mijn excuses voor de chaos. Er zit een error in als je low skilled wage workers toevoegd in het model, ik wilde hier woensdagochtend (europese tijd) naar kijken. De error is ontstaan toen ik van mijn low skilled agents migrated agents probeerde te maken (regel 198 in agents2.py)

This model simulates the inhabitants of the Mekong Delta in Vietnam. In the final version, there will be different types of houehold agents:
- Agri farmer agents. These are small, middle size and corporate farmers. These are the households who own land and cultivate rice, vegetables etc. 
- Aqua farmer agents. These are small or large farmers, and they have their own shrimps.
- Wage worker agents. These households work in agri or aqua, and do not have their own farm.
- Service agents. They do not work in the agri or aqua sector. 
- Migrated agents. This is the group of people who migrated to the city. 
- Mix households. These agents have some members working in wage, and some in service. 

The Agents2.py file consists of the agents and their activities. The step function refers to functions in the Functions2.py file. To run the model, model_run2.ipynb can be run. 