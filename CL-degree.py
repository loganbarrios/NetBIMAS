import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from scipy.stats import chisquare

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

# Connect nodes with shared endpoints
path_groups = defaultdict(list)
for _, row in df.iterrows():
    path_groups[row['end-coords']].append(f"Cell-{row['who']}")
for group in path_groups.values():
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            G.add_edge(group[i], group[j], weight=1.0)

# ----------------------
# Chung–Lu Null Models
# ----------------------
num_nulls = 10000
degrees_empirical = [deg for _, deg in G.degree()]
null_degree_distributions = []

for _ in range(num_nulls):
    G_null = nx.expected_degree_graph(degrees_empirical, selfloops=False)
    degree_counts = Counter(dict(G_null.degree()).values())
    null_degree_distributions.append(degree_counts)

# ----------------------
# Aggregate Null Degree Frequencies
# ----------------------
all_degrees = sorted(set(deg for dist in null_degree_distributions for deg in dist))
degree_freq_null = {deg: [] for deg in all_degrees}

for dist in null_degree_distributions:
    for deg in all_degrees:
        degree_freq_null[deg].append(dist.get(deg, 0))

degree_null_mean = {k: np.mean(v) for k, v in degree_freq_null.items()}
degree_null_std = {k: np.std(v) for k, v in degree_freq_null.items()}

# ----------------------
# Empirical Degree Distribution
# ----------------------
empirical_degree_counts = Counter(dict(G.degree()).values())

# ----------------------
# Plotting: Empirical vs. Null Degree Distribution
# ----------------------
degrees = sorted(degree_null_mean.keys())
empirical = [empirical_degree_counts.get(d, 0) for d in degrees]
mean_null = [degree_null_mean[d] for d in degrees]
std_null = [degree_null_std[d] for d in degrees]

plt.errorbar(degrees, mean_null, yerr=std_null, fmt='o', label='Chung–Lu Null (mean ± SD)', color='gray', capsize=4)
plt.plot(degrees, empirical, 'o-', label='Empirical', color='red')
plt.xlabel('Degree')
plt.ylabel('Number of Nodes')
plt.title('Degree Distribution: Empirical vs. Chung–Lu Null')
plt.legend()
plt.tight_layout()
plt.savefig("degree_distribution_comparison.png", dpi=300)
plt.show()

# ----------------------
# Optional: Chi-square test
# ----------------------
# Ensure both vectors are aligned and non-zero in null expected values
chi_degrees = [d for d in degrees if degree_null_mean[d] > 0]
empirical_vals = [empirical_degree_counts.get(d, 0) for d in chi_degrees]
expected_vals = [degree_null_mean[d] for d in chi_degrees]

chi2_stat, p_val = chisquare(f_obs=empirical_vals, f_exp=expected_vals)
print(f"Chi-square statistic: {chi2_stat:.2f}")
print(f"p-value: {p_val:.4f}")
