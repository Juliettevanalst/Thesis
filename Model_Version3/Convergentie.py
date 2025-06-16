import pandas as pd
import matplotlib.pyplot as plt
from Model3 from  RiverDeltaModel
params = {"num_agents":[1000]}

result_batch = batch_run(
    RiverDeltaModel,
    parameters=params,
    iterations=500,
    max_steps=300,
    number_processes= None,
    data_collection_period=3,
    display_progress=True,
)
df = pd.DataFrame(result_batch)
df = df[df["Step"]==df["Step"].max()]
df = df.reset_index()

# List of metrics to plot
metrics = ['Annual crops agents', "Migrated_households"]

# Assume df is your DataFrame containing these metrics

# Calculate running mean and standardize for each metric
for metric in metrics:
    df[f'{metric}_running_mean'] = df[metric].expanding().mean()
    mean = df[f'{metric}_running_mean'].mean()
    std = df[f'{metric}_running_mean'].std()
    df[f'{metric}_standardized'] = (df[f'{metric}_running_mean'] - mean) / std

# Plotting on 2x2 subplots
fig, axs = plt.subplots(2, 1, figsize=(12, 10))
axs = axs.flatten()

for idx, metric in enumerate(metrics):
    axs[idx].plot(df.index + 1, df[f'{metric}_standardized'], label=f'Std Running Mean: {metric}')
    # Add the 0.5 and -0.5 red reference lines with one shared label
    axs[idx].axhline(1, color="blue", linestyle="--", linewidth=1)
    axs[idx].axhline(-1, color="blue", linestyle="--", linewidth=1, label="One standardevation threshold")
    axs[idx].set_title(f'Convergence: {metric}')
    axs[idx].set_xlabel('Model Run')
    axs[idx].set_ylabel('Standardized Running Mean')
    axs[idx].grid(True)

    # Add both plot and reference line to the legend
    axs[idx].legend()

plt.tight_layout()
plt.show()