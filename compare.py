import pandas as pd
import networkx as nx
import numpy as np
from scipy.spatial.distance import euclidean
from networkx.algorithms.community import modularity
import matplotlib.pyplot as plt

def analyze_simulation(file_path):
    df = pd.read_csv(file_path)
    df = df[df['who'] != 'who']  # Remove header rows
    numeric_cols = ['who', 'tick', 'start-x', 'start-y', 'end-x', 'end-y', 'total-distance', 'straight-line', 'efficiency']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=numeric_cols)
    df = df.sort_values(by='tick').drop_duplicates(subset='who', keep='last').reset_index(drop=True)

    # Assign quadrant
    def assign_quadrant(x, y):
        if x > 0 and y > 0: return 'Q1'
        elif x < 0 and y < 0: return 'Q3'
        else: return 'Other'
    df['quadrant'] = df.apply(lambda row: assign_quadrant(row['end-x'], row['end-y']), axis=1)

    # Build network
    G = nx.Graph()
    for _, row in df[df['quadrant'].isin(['Q1', 'Q3'])].iterrows():
        node = f"Cell-{row['who']}"
        G.add_node(node)
        G.nodes[node]['quadrant'] = row['quadrant']

    # Connect nodes with same end coords (shared paths)
    df['end-coords'] = list(zip(df['end-x'].round(3), df['end-y'].round(3)))
    from collections import defaultdict
    path_groups = defaultdict(list)
    for _, row in df.iterrows():
        path_groups[row['end-coords']].append(f"Cell-{row['who']}")
    for group in path_groups.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                G.add_edge(group[i], group[j], weight=1.0)

    # Compute metrics
    global_eff = nx.global_efficiency(G)
    clustering = nx.average_clustering(G)

    q_eff = {}
    for q in ['Q1', 'Q3']:
        nodes_q = [n for n in G.nodes if G.nodes[n].get('quadrant') == q]
        subG = G.subgraph(nodes_q)
        q_eff[q] = nx.global_efficiency(subG) if len(nodes_q) > 1 else np.nan

    community_q1 = {n for n in G.nodes if G.nodes[n].get('quadrant') == 'Q1'}
    community_q3 = {n for n in G.nodes if G.nodes[n].get('quadrant') == 'Q3'}
    mod = modularity(G, [community_q1, community_q3])

    return {
        'global_eff': global_eff,
        'q1_eff': q_eff['Q1'],
        'q3_eff': q_eff['Q3'],
        'modularity': mod,
        'clustering': clustering,
        'n_q1': len(community_q1),
        'n_q3': len(community_q3),
    }

# Run on both CSVs
result1 = analyze_simulation("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/1-bacteria-path-data.csv")
result2 = analyze_simulation("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/2-bacteria-path-data.csv")

# Compare
comparison = pd.DataFrame([result1, result2], index=['Run 1', 'Run 2'])
print(comparison)

# ----------------------------
# Combined Degree Distribution
# ----------------------------

def get_degrees(file_path):
    df = pd.read_csv(file_path)
    df = df[df['who'] != 'who']
    numeric_cols = ['who', 'tick', 'start-x', 'start-y', 'end-x', 'end-y', 'total-distance', 'straight-line', 'efficiency']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=numeric_cols)
    df = df.sort_values(by='tick').drop_duplicates(subset='who', keep='last').reset_index(drop=True)
    df['end-coords'] = list(zip(df['end-x'].round(3), df['end-y'].round(3)))

    G = nx.Graph()
    for _, row in df.iterrows():
        node = f"Cell-{row['who']}"
        G.add_node(node)

    from collections import defaultdict
    path_groups = defaultdict(list)
    for _, row in df.iterrows():
        path_groups[row['end-coords']].append(f"Cell-{row['who']}")
    for group in path_groups.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                G.add_edge(group[i], group[j], weight=1.0)

    degrees = [deg for node, deg in G.degree()]
    return degrees

# Collect degrees from both simulations
deg1 = get_degrees("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/1-bacteria-path-data.csv")
deg2 = get_degrees("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/2-bacteria-path-data.csv")

# Combine degrees
all_degrees = deg1 + deg2

# Plot histogram
from collections import Counter
degree_counts = Counter(all_degrees)
degrees, counts = zip(*sorted(degree_counts.items()))

plt.bar(degrees, counts, color='skyblue', edgecolor='black')
plt.xlabel("Degree")
plt.ylabel("Number of Nodes")
plt.title("Combined Degree Distribution of Cyanobacteria Networks")
plt.xticks(degrees)
plt.tight_layout()
plt.show()

# -------------------------------------------
# Subgraph Community Analysis: Q1 and Q3
# -------------------------------------------
def analyze_community_subgraph(file_path):
    df = pd.read_csv(file_path)
    df = df[df['who'] != 'who']
    numeric_cols = ['who', 'tick', 'start-x', 'start-y', 'end-x', 'end-y', 'total-distance', 'straight-line', 'efficiency']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=numeric_cols)
    df = df.sort_values(by='tick').drop_duplicates(subset='who', keep='last').reset_index(drop=True)
    df['end-coords'] = list(zip(df['end-x'].round(3), df['end-y'].round(3)))

    def assign_quadrant(x, y):
        if x > 0 and y > 0: return 'Q1'
        elif x < 0 and y < 0: return 'Q3'
        else: return 'Other'
    df['quadrant'] = df.apply(lambda row: assign_quadrant(row['end-x'], row['end-y']), axis=1)

    G = nx.Graph()
    node_quadrants = {}

    for _, row in df[df['quadrant'].isin(['Q1', 'Q3'])].iterrows():
        node = f"Cell-{row['who']}"
        G.add_node(node)
        node_quadrants[node] = row['quadrant']

    from collections import defaultdict
    path_groups = defaultdict(list)
    for _, row in df.iterrows():
        path_groups[row['end-coords']].append(f"Cell-{row['who']}")
    for group in path_groups.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                G.add_edge(group[i], group[j], weight=1.0)

    metrics = {}
    for q in ['Q1', 'Q3']:
        sub_nodes = [n for n, qd in node_quadrants.items() if qd == q]
        subG = G.subgraph(sub_nodes)
        eff = nx.global_efficiency(subG)
        clust = nx.average_clustering(subG)
        try:
            path_len = nx.average_shortest_path_length(subG)
        except nx.NetworkXError:
            path_len = np.nan
        close = nx.closeness_centrality(subG)
        between = nx.betweenness_centrality(subG)

        metrics[q] = {
            'efficiency': eff,
            'avg_clustering': clust,
            'avg_path_length': path_len,
            'avg_closeness': np.mean(list(close.values())),
            'avg_betweenness': np.mean(list(between.values())),
            'num_nodes': len(sub_nodes)
        }

    return metrics

# Analyze both runs
metrics1 = analyze_community_subgraph("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/1-bacteria-path-data.csv")
metrics2 = analyze_community_subgraph("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/2-bacteria-path-data.csv")

# Display as DataFrame
community_df = pd.DataFrame({
    'Run 1 - Q1': metrics1['Q1'],
    'Run 1 - Q3': metrics1['Q3'],
    'Run 2 - Q1': metrics2['Q1'],
    'Run 2 - Q3': metrics2['Q3']
}).T

print("\nCommunity-Level Metrics:")
print(community_df.round(4))
