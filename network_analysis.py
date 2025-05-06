import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import euclidean

# --------------------
# Load and clean the data
# --------------------
df = pd.read_csv("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/1-bacteria-path-data.csv")

# Remove any repeated header rows
df = df[df['who'] != 'who']

# Convert all relevant columns to numeric
numeric_cols = ['who', 'tick', 'start-x', 'start-y', 'end-x', 'end-y', 'total-distance', 'straight-line', 'efficiency']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

# Drop any rows with NaNs after conversion
# Drop any rows with NaNs after conversion
df = df.dropna(subset=numeric_cols)

# Keep only most recent data per bacterium
df = df.sort_values(by='tick') \
       .drop_duplicates(subset='who', keep='last') \
       .reset_index(drop=True)

# Assign quadrant based on final location
def assign_quadrant(x, y):
    if x > 0 and y > 0:
        return 'Q1'
    elif x < 0 and y > 0:
        return 'Q2'
    elif x < 0 and y < 0:
        return 'Q3'
    elif x > 0 and y < 0:
        return 'Q4'
    else:
        return 'Other'

df['quadrant'] = df.apply(lambda row: assign_quadrant(row['end-x'], row['end-y']), axis=1)
# Assign a rounded endpoint coordinate to group identical paths
df['end-coords'] = list(zip(df['end-x'].round(3), df['end-y'].round(3)))


# --------------------
# Build Network: Nest and Cyanobacteria Nodes
# --------------------
G = nx.Graph()
G.add_node('Nest')

# Add bacterium nodes and connect to Nest
for _, row in df[df['quadrant'].isin(['Q1', 'Q3'])].iterrows():
    target = f"Cell-{row['who']}"
    G.add_node(target, pos=(row['end-x'], row['end-y']))
    G.add_edge('Nest', target, weight=row['total-distance'])  # could use 'straight-line'

# --------------------
# Add edges between bacteria with similar endpoints
# --------------------
# --------------------
# Add edges between bacteria with similar endpoints
# --------------------
# --------------------
# Add edges only between bacteria in the same quadrant
# --------------------
#threshold = 1.0  # spatial distance threshold
#df = df.reset_index(drop=True)

#for q in ['Q1', 'Q3']:
#    df_q = df[df['quadrant'] == q].reset_index(drop=True)
#    for i, row1 in df_q.iterrows():
#        for j in range(i + 1, len(df_q)):
#            row2 = df_q.iloc[j]
#            node1 = f"Cell-{row1['who']}"
#            node2 = f"Cell-{row2['who']}"
#
#            if node1 == node2:
#                continue
#
#            dist = euclidean((row1['end-x'], row1['end-y']), (row2['end-x'], row2['end-y']))
#            if dist <= threshold and not G.has_edge(node1, node2):
#                G.add_edge(node1, node2, weight=1 / (dist + 1e-6))  # safe inverse distance
from collections import defaultdict

# Group nodes by identical end-coords (shared path)
path_groups = defaultdict(list)

for _, row in df[df['quadrant'].isin(['Q1', 'Q3'])].iterrows():
    node = f"Cell-{row['who']}"
    path_groups[row['end-coords']].append(node)

# Connect all nodes that share the exact path
for group in path_groups.values():
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            node1, node2 = group[i], group[j]
            if not G.has_edge(node1, node2):
                G.add_edge(node1, node2, weight=1.0)

# --------------------
# Efficiency & Degree
# --------------------
efficiency = nx.global_efficiency(G)
print(f"Global Network Efficiency: {efficiency:.4f}")

avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
print(f"Average Degree: {avg_degree:.2f}")

# --------------------
# Plot Network
# --------------------
# --------------------
# Custom cluster layout by quadrant
# --------------------

# Start with Nest in the middle
# --------------------
# Tighter cluster layout by quadrant
# --------------------

# Place the Nest in the center
# Nest in center
pos = {'Nest': (0, 0)}

# Q1: upper right, tight grid
for i, row in enumerate(df[df['quadrant'] == 'Q1'].itertuples()):
    pos[f"Cell-{row.who}"] = (1.5 + (i % 5), 1.5 + (i // 5))

# Q3: lower left, tight grid
for i, row in enumerate(df[df['quadrant'] == 'Q3'].itertuples()):
    pos[f"Cell-{row.who}"] = (-1.5 - (i % 5), -1.5 - (i // 5))


#pos = nx.spring_layout(G, k=2, seed=42)  # Larger k spreads out nodes
#nx.draw(G, pos, with_labels=True, node_size=300, font_size=8)
#nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'weight'))
# --------------------
# Color nodes by quadrant category
# --------------------
color_map = []
for node in G.nodes():
    if node == 'Nest':
        color_map.append('gray')  # or 'white'
    else:
        # Extract agent ID from node label
        agent_id = int(node.replace('Cell-', ''))
        quadrant = df[df['who'] == agent_id]['quadrant'].values[0]
        if quadrant == 'Q1':
            color_map.append('red')
        elif quadrant == 'Q3':
            color_map.append('blue')
        else:
            color_map.append('black')  # fallback, shouldn't happen if filtered correctly
# Simplified labels: just numbers
labels = {}
for node in G.nodes():
    if node == 'Nest':
        labels[node] = 'Nest'
    else:
        labels[node] = node.replace('Cell-', '')

# Draw the network
nx.draw(G, pos, labels=labels, node_color=color_map, node_size=250, font_size=8,
        edgecolors='black')
#nx.draw(G, pos, with_labels=True, node_color=color_map, node_size=300, font_size=8)
plt.axis('off')
plt.tight_layout()
plt.title("Cyanobacteria Movement Network with Shared Endpoints")
plt.show()

G_no_nest = G.copy()
G_no_nest.remove_node('Nest')

from collections import Counter

# Get degree of all nodes (excluding Nest if you prefer)
degrees = [deg for node, deg in G.degree() if node != 'Nest']

# Count how many nodes have each degree
degree_counts = Counter(degrees)

# Sort by degree
degree_distribution = sorted(degree_counts.items())  # list of (degree, count)
print("Degree distribution (degree: count):")
for degree, count in degree_distribution:
    print(f"  {degree}: {count}")
degrees, counts = zip(*degree_distribution)
plt.bar(degrees, counts, color='skyblue', edgecolor='black')
plt.xlabel("Degree")
plt.ylabel("Number of Nodes")
plt.title("Degree Distribution of Cyanobacteria Network")
plt.xticks(degrees)
plt.show()

# -----------------------------
# Improved Categorical Histogram: Clustering Coefficients by Quadrant
# -----------------------------
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Get clustering values per node in each quadrant
clustering_data = {}
unique_vals = set()

for q in ['Q1', 'Q3']:
    q_nodes = [f"Cell-{row['who']}" for _, row in df[df['quadrant'] == q].iterrows()]
    subG = G.subgraph(q_nodes)
    clustering_vals = list(nx.clustering(subG).values())
    
    # Round for categorical binning (e.g., 0.0, 0.33, 0.5, 1.0)
    clustering_rounded = [round(v, 2) for v in clustering_vals]
    counts = Counter(clustering_rounded)
    clustering_data[q] = counts
    unique_vals.update(counts.keys())

# Sort unique clustering coefficient bins
sorted_vals = sorted(unique_vals)

# Prepare bar heights
q1_counts = [clustering_data['Q1'].get(v, 0) for v in sorted_vals]
q3_counts = [clustering_data['Q3'].get(v, 0) for v in sorted_vals]

x = np.arange(len(sorted_vals))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(x - width/2, q1_counts, width, label='Q1', color='red', edgecolor='black')
ax.bar(x + width/2, q3_counts, width, label='Q3', color='blue', edgecolor='black')

# Labeling
ax.set_xticks(x)
ax.set_xticklabels(sorted_vals)
ax.set_xlabel("Clustering Coefficient")
ax.set_ylabel("Number of Nodes")
ax.set_title("Clustering Coefficient Distribution by Quadrant")
ax.legend()
plt.tight_layout()
plt.savefig("clustering_categorical_by_quadrant.png", dpi=300)
plt.show()



if nx.is_connected(G):
    print(f"Diameter: {nx.diameter(G_no_nest)}")
    print(f"Average Path Length: {nx.average_shortest_path_length(G_no_nest):.4f}")
else:
    print("Graph is not connected; computing diameter on largest component...")
    largest_cc = G_no_nest.subgraph(max(nx.connected_components(G_no_nest), key=len))
    print(f"Diameter (Largest Component): {nx.diameter(largest_cc)}")
    print(f"Avg Path Length (Largest Component): {nx.average_shortest_path_length(largest_cc):.4f}")

eff = nx.global_efficiency(G_no_nest)
print(f"Global Efficiency: {eff:.4f}")


# --------------------
# Null Model: Randomized Endpoints
# --------------------
def random_endpoint_null(df, n=1000):
    efficiencies = []
    for _ in range(n):
        G_null = nx.Graph()
        G_null.add_node('Nest')
        for _, row in df.iterrows():
            target = f"Null-{row['who']}"
            G_null.add_node(target)
            rand_end = np.random.uniform(-20, 20, size=2)
            straight_line = np.sqrt((row['start-x'] - rand_end[0])**2 + (row['start-y'] - rand_end[1])**2)
            G_null.add_edge('Nest', target, weight=straight_line)
        eff = nx.global_efficiency(G_null)
        efficiencies.append(eff)
    return efficiencies

# --------------------
# Plot Null Distribution
# --------------------
null_eff = random_endpoint_null(df)
plt.hist(null_eff, bins=30, alpha=0.7)
plt.axvline(efficiency, color='red', linestyle='--', label='Observed Efficiency')
plt.legend()
plt.title("Global Efficiency vs Null Model")
plt.xlabel("Efficiency")
plt.ylabel("Frequency")
plt.show()

closeness = nx.closeness_centrality(G_no_nest)
degree = dict(G_no_nest.degree())

for q in ['Q1', 'Q3']:
    nodes = [f"Cell-{row['who']}" for _, row in df[df['quadrant'] == q].iterrows()]
    subG = G.subgraph(nodes)

    closeness = nx.closeness_centrality(subG)
    degree = dict(subG.degree())

    print(f"\n{q} Centrality Metrics:")
    for node in sorted(subG.nodes()):
        print(f"  {node.replace('Cell-', '')}: Degree={degree[node]}, Closeness={closeness[node]:.3f}")

fig, ax = plt.subplots(1, 2, figsize=(12, 5))

for i, q in enumerate(['Q1', 'Q3']):
    nodes = [f"Cell-{row['who']}" for _, row in df[df['quadrant'] == q].iterrows()]
    subG = G.subgraph(nodes)

    degree = dict(subG.degree())
    closeness = nx.closeness_centrality(subG)

    ax[i].scatter(list(degree.values()), list(closeness.values()), color='red' if q=='Q1' else 'blue')
    ax[i].set_title(f"{q}: Degree vs Closeness")
    ax[i].set_xlabel("Degree")
    ax[i].set_ylabel("Closeness")

plt.tight_layout()
plt.show()

for q in ['Q1', 'Q3']:
    q_nodes = [f"Cell-{row['who']}" for _, row in df[df['quadrant'] == q].iterrows()]
    subG = G.subgraph(q_nodes)
    eff_q = nx.global_efficiency(subG)
    print(f"Efficiency in {q}: {eff_q:.4f}")
