Created by Juliëtte van Alst

This model simulates the inhabitants of the Mekong Delta in Vietnam. Model version3 is the newest version of the model. It is recommended to download model_version3 and the requirements.txt(hope it works). 
The model uses data from the pop housing census 2009 and 2020 and VHLSS2020. The input data for a certain district (in this case 823) can be found in the "Data" folder in Model_Version3. 
To run the model you need to run model_run.ipynb. 

Sidenote: Op dit moment zijn de kosten van mais te hoog, en moet een gevoeligheidsanalyse  nog gedaan worden. Ook moeten nog een paar beslisregels worden toegepast, maar in hoofdlijnen is dit het model

Er is ergens een zwakke referentie, in 99% vande gevallen gaat het goed, maar soms gaat het mis en ik snap niet zo goed waardoor? ik heb het nu opgelost door .discard ipv .remove te gebruiken als ik mijn agents verwijder, en eerst te checken of de agent household_member wel diens huishouden zit. Zoals bijv in agents3.py regel 223 tm 231. 

Nog toevoegen:
- als je machines gebruikt heb je minder wage workers nodig
- maize en shrimp moet ook een waiting time. nu is het mogelijk om gelijk uit je rijst ook shrimp te oogsten, ipv dat het eerst 6 maanden groeit
- als je 17+ bent als non_labourer moet je ook gaan werken, nu blijf je studeren en blijf je daarna non labourer
- De std dev van de death_age staat te hoog, veel mensen gaan al jong dood
- je crop yield ligt aan je educatie level, als die hoger is is je yield 10% hoger
