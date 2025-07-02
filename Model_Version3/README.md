This map contains all the files to run the ABM ones, but also the model output with 150 runs, sensitivity analysis, verification, and extreme value testing.  

The "Model_run3.ipynb" file can be used to run the model 1 time, look at a lot of different output values over time, and look at the agents on the map.
The "Convergence and model output.ipynb" file looks at the required number of runs, and runs the model 150 times using a batchrunner. 
The "Extreme value testing" map has separate models to look at the extreme values, and the sensitivity of the models to the extreme values. This can be run by running the "Extreme_value_test.ipynb" file. 
All data which is required to run the model is in the "Data" map. 

It is important to note that there are a lot of variables in the datacollector, these are defined in Model3.py between line 230-450. Before running the analyses, it is recommended to first look which model and agent_reporters are needed, before running everything. This will save a lot of runtime :)

There is a large limitation in the experiments and verification file: I would recommend to run this with a batchrunner in the future, instead of only running it for 1 time (due to the stochastic features). 


