Created by Juliëtte van Alst

This model simulates the inhabitants of the Mekong Delta in Vietnam. Model version3 is the newest version of the model. It is recommended to download model_version3. 
The model uses data from the pop housing census 2009 and 2020 and VHLSS2014. The input data for a certain district (in this case 894) can be found in the "Data" folder in Model_Version3. 
To run the model you need to run model_run.ipynb. 

De grootste problemen op dit moment zijn denk ik:
- In sommige districts zijn er heel veel rijst agents, terwijl er in die regio vooral zoute gebieden zijn. Men trekt dan direct weg, omdat ik ze random op de kaart plaats
    --> dit kan opgelost worden door de rijst mensen op de kaart te plaatsen op basis van salinity level
- De rijst mensen trekken weg, maar annual crops farmers blijven. Dit komt doordat de data die ik voor de crops gebruik verzameld is van allemaal verschillende literatuur
    --> dit kan getweakt worden
    --> dit is ook waardoor sommige kokosnoot farmers ineens rijk zijn volgens mij
- Wage workers krijgen veel te veel betaald --> kan ook getweakt worden