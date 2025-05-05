import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict, Counter

# ---------- Load and clean data ----------
df = pd.read_csv("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/1-bacteria-path-data.csv")
df = df[df['who'] != 'who']  # Remove duplicate headers
numeric_cols = ['who', 'tick', 'start-x', 'start-y', 'end-x', 'end-y', 'total-distance', 'straight-line', 'efficiency']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=numeric_cols)

# Keep only latest data per agent
df = df.sort_values(by='tick').drop_duplicates(subset='who', keep='last').reset_index(drop=True)

# Round endpoints to group shared paths
df['end-coords'] = list(zip(df['end-x'].round(3), df['end-y'].round(3)))

# ---------- Build graph ----------
G = nx.Graph()
for _, row in df.iterrows():
    G.add_node(f"Cell-{row['who']}", pos=(row['end-x'], row['end-y']))

# Connect nodes with same endpoint
path_groups = defaultdict(list)
for _, row in df.iterrows():
    path_groups[row['end-coords']].append(f"Cell-{row['who']}")
for group in path_groups.values():
    for i in range(len(group)):
        for j in range(i+1, len(group)):
            G.add_edge(group[i], group[j], weight=1.0)

# ---------- Network statistics ----------
print("=== Network Summary ===")
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")

degrees = dict(G.degree())
avg_degree = np.mean(list(degrees.values()))
print(f"Average Degree: {avg_degree:.2f}")

clustering = nx.average_clustering(G)
print(f"Average Clustering Coefficient: {clustering:.4f}")

if nx.is_connected(G):
    print(f"Diameter: {nx.diameter(G)}")
    print(f"Average Path Length: {nx.average_shortest_path_length(G):.4f}")
else:
    print("Graph is not connected; computing diameter on largest component...")
    largest_cc = G.subgraph(max(nx.connected_components(G), key=len))
    print(f"Diameter (Largest Component): {nx.diameter(largest_cc)}")
    print(f"Avg Path Length (Largest Component): {nx.average_shortest_path_length(largest_cc):.4f}")

eff = nx.global_efficiency(G)
print(f"Global Efficiency: {eff:.4f}")

# ---------- Degree Distribution ----------
deg_counts = Counter(degrees.values())
deg_x, deg_y = zip(*sorted(deg_counts.items()))

plt.figure(figsize=(6,4))
plt.bar(deg_x, deg_y, color='skyblue', edgecolor='black')
plt.xlabel("Degree")
plt.ylabel("Number of Nodes")
plt.title("Degree Distribution")
plt.tight_layout()
plt.show()

# ---------- Draw Graph ----------
plt.figure(figsize=(8, 6))
pos = nx.spring_layout(G, seed=42)
nx.draw(G, pos, node_size=300, node_color='lightcoral', edgecolors='black', with_labels=True, font_size=8)
plt.title("Cyanobacteria Shared Path Network")
plt.axis('off')
plt.tight_layout()
plt.show()
