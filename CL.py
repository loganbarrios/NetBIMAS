import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
from collections import defaultdict, Counter

# ----------------------
# Load and clean the data
# ----------------------
df = pd.read_csv("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/1-bacteria-path-data.csv")
df = df[df['who'] != 'who']
numeric_cols = ['who', 'tick', 'start-x', 'start-y', 'end-x', 'end-y', 'total-distance', 'straight-line', 'efficiency']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=numeric_cols)
df = df.sort_values(by='tick').drop_duplicates(subset='who', keep='last').reset_index(drop=True)
df['end-coords'] = list(zip(df['end-x'].round(3), df['end-y'].round(3)))

# ----------------------
# Build Empirical Network
# ----------------------
G = nx.Graph()
for _, row in df.iterrows():
    node = f"Cell-{row['who']}"
    G.add_node(node)
# Group by shared endpoints
path_groups = defaultdict(list)
for _, row in df.iterrows():
    path_groups[row['end-coords']].append(f"Cell-{row['who']}")
for group in path_groups.values():
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            G.add_edge(group[i], group[j], weight=1.0)

# ----------------------
# Chung-Lu Null Models
# ----------------------
num_nulls = 10000
degrees = [deg for _, deg in G.degree()]
null_clustering = []
null_efficiencies = []

for _ in range(num_nulls):
    G_null = nx.expected_degree_graph(degrees, selfloops=False)
    null_clustering.append(nx.average_clustering(G_null))
    if nx.is_connected(G_null):
        null_efficiencies.append(nx.global_efficiency(G_null))
    else:
        # take the largest connected component
        largest_cc = max(nx.connected_components(G_null), key=len)
        G_sub = G_null.subgraph(largest_cc)
        null_efficiencies.append(nx.global_efficiency(G_sub))

# ----------------------
# Real Network Metrics
# ----------------------
real_clustering = nx.average_clustering(G)
real_efficiency = nx.global_efficiency(G)

print(f"Empirical Clustering: {real_clustering:.4f}")
print(f"Empirical Global Efficiency: {real_efficiency:.4f}")

# ----------------------
# Degree vs Distance
# ----------------------
node_to_distance = {
    f"Cell-{row['who']}": row['total-distance']
    for _, row in df.iterrows()
}
degrees = dict(G.degree())
degree_list = []
distance_list = []

for node in G.nodes():
    if node in node_to_distance:
        degree_list.append(degrees[node])
        distance_list.append(node_to_distance[node])

rho, pval = spearmanr(degree_list, distance_list)
print(f"Spearman Correlation (Degree vs Distance): rho = {rho:.3f}, p = {pval:.4f}")

# ----------------------
# Visualizations
# ----------------------
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# Left: Clustering Distribution
ax[0].hist(null_clustering, bins=20, alpha=0.7, label='Chung-Lu Null')
ax[0].axvline(real_clustering, color='red', linestyle='--', label='Empirical')
ax[0].set_title("Clustering Coefficient")
ax[0].set_xlabel("Average Clustering")
ax[0].set_ylabel("Frequency")
ax[0].legend()

# Right: Degree vs Distance (scatter)
ax[1].scatter(degree_list, distance_list, alpha=0.7, s=40, c='green')
ax[1].set_xlabel("Degree")
ax[1].set_ylabel("Travel Distance")
ax[1].set_title("Degree vs. Travel Distance")

plt.tight_layout()
plt.show()
plt.savefig("degree_vs_distance.png", dpi=300)
