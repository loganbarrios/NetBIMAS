from graph_tool.all import *
import pandas as pd

# Load and clean data
df = pd.read_csv("/Users/loganbarrios/NetBIMAS/Simulation_Runs_2lights/1-bacteria-path-data.csv")
df = df[df['who'] != 'who']
numeric_cols = ['who', 'tick', 'start-x', 'start-y', 'end-x', 'end-y', 'total-distance', 'straight-line', 'efficiency']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=numeric_cols)
df = df.sort_values(by='tick').drop_duplicates(subset='who', keep='last').reset_index(drop=True)

# Build graph-tool network
g = Graph()
who_to_vertex = {}
for who in df['who']:
    v = g.add_vertex()
    who_to_vertex[int(who)] = v

# Add edges for identical paths
df['end-coords'] = list(zip(df['end-x'].round(3), df['end-y'].round(3)))
from collections import defaultdict
groups = defaultdict(list)
for _, row in df.iterrows():
    groups[row['end-coords']].append(int(row['who']))

for group in groups.values():
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            g.add_edge(who_to_vertex[group[i]], who_to_vertex[group[j]])

# Run Degree-Corrected SBM
state = minimize_blockmodel_dl(g, deg_corr=True)
b = state.get_blocks()
print(f"Number of communities: {len(set(b.a))}")

# Draw the graph
graph_draw(g, vertex_fill_color=b, output_size=(800, 800))
