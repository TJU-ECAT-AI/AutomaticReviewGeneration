import glob
import json
import os
import re
import warnings
from collections import defaultdict
from itertools import combinations
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pingouin as pg
warnings.filterwarnings("ignore")
def process_json(data):
    rows = []
    for category, subcategories in data.items():
        if category != 'Overall Evaluation':
            for subcategory, details in subcategories.items():
                row = {
                    'Category': category,
                    'Subcategory': subcategory if not subcategory.startswith(
                        'Feasibility') else 'Feasibility of Proposed Suggestions',
                    'Review A Score': details.get('Review A Score', ''),
                    'Review B Score': details.get('Review B Score', ''),
                }
                rows.append(row)
    return rows
def process_file(file_path):
    with open(file_path, 'r') as file:
        json_data = json.loads('{' + file.read().split('{', 1)[1].rsplit('}', 1)[0] + '}')
    processed_data = process_json(json_data)
    df = pd.DataFrame(processed_data)
    file_name = os.path.basename(file_path)
    a, b = file_name.split('@')
    a = a.split('_', 1)[1]
    b = b.split('.')[0]
    df['A'] = a
    df['B'] = b
    df['File'] = file_name
    return df
def create_analysis_df():
    target_dir = os.path.join('..', 'Temp', 'ReviewCompositionWorkDir', 'Paragraph', 'CompareParagraph')
    target_dir = os.path.abspath(target_dir)
    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"Target directory not found: {target_dir}")
    file_pattern = os.path.join(target_dir, "Comparison*_Paragraph*_*@Paragraph*_*.txt")
    all_files = glob.glob(file_pattern)
    print(f"Found {len(all_files)} files matching the pattern")
    all_files = [f for f in all_files if
                 re.match(r'Comparison\d_Paragraph\d+_\d+@Paragraph\d+_\d+\.txt$', os.path.basename(f))]
    print(f"After filtering, {len(all_files)} files remain")
    all_data = []
    for file_path in all_files:
        try:
            file_df = process_file(file_path)
            all_data.append(file_df)
            print(f"Successfully processed: {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    if not all_data:
        raise ValueError("No data was processed from the files")
    df = pd.concat(all_data, ignore_index=True)
    Subcategorys = file_df.Subcategory.values
    df['Review A Score'] = pd.to_numeric(df['Review A Score'], errors='coerce')
    df['Review B Score'] = pd.to_numeric(df['Review B Score'], errors='coerce')
    df['Comparison'] = df['File'].apply(lambda x: re.search(r'Comparison(\d+)', x).group(1))
    df['Paragraph A'] = df['A'].apply(lambda x: re.search(r'Paragraph(\d+)_(\d+)', x).group(1))
    df['Author A'] = df['A'].apply(lambda x: re.search(r'Paragraph(\d+)_(\d+)', x).group(2))
    df['Paragraph B'] = df['B'].apply(lambda x: re.search(r'Paragraph(\d+)_(\d+)', x).group(1))
    df['Author B'] = df['B'].apply(lambda x: re.search(r'Paragraph(\d+)_(\d+)', x).group(2))
    df['Subcategory'] = df['Subcategory'].replace('Feasibility of Policy Suggestions',
                                                  'Feasibility of Proposed Suggestions')
    return df, Subcategorys
def calculate_relative_score_diff(score_a, score_b):
    if score_a == score_b == 0:
        return 0
    elif score_a == 0:
        return -1
    elif score_b == 0:
        return 1
    else:
        return (score_a - score_b) / max(score_a, score_b)
def build_graph(subcategory_data):
    graph = defaultdict(lambda: defaultdict(list))
    nodes = set()
    for _, row in subcategory_data.iterrows():
        a, b = f"{row['Paragraph A']}_{row['Author A']}", f"{row['Paragraph B']}_{row['Author B']}"
        nodes.add(a)
        nodes.add(b)
        rel_score_diff = calculate_relative_score_diff(row['Review A Score'], row['Review B Score'])
        graph[a][b].append(rel_score_diff)
        graph[b][a].append(-rel_score_diff)
    for node in graph:
        for neighbor in graph[node]:
            graph[node][neighbor] = np.mean(graph[node][neighbor])
    return dict(graph), list(nodes)
def pagerank(graph, nodes, damping=0.85, iterations=1000, tolerance=1e-6):
    n = len(nodes)
    if n == 0:
        return {}
    ranks = {node: 1 / n for node in nodes}
    for i in range(iterations):
        new_ranks = {}
        total_diff = 0
        for node in nodes:
            rank_sum = 0
            for neighbor, weight in graph[node].items():
                out_sum = sum(abs(w) for w in graph[neighbor].values())
                if out_sum > 0:
                    rank_sum += weight * ranks[neighbor] / out_sum
            new_rank = (1 - damping) / n + damping * rank_sum
            new_ranks[node] = new_rank
            total_diff += abs(new_rank - ranks[node])
        ranks = new_ranks
        if total_diff < tolerance:
            break
    return ranks
def convert_to_0_10_scale(scores):
    min_score = min(scores.values())
    max_score = max(scores.values())
    if min_score == max_score:
        return {k: 5 for k in scores}
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))
    relative_positions = {k: (v - min_score) / (max_score - min_score) for k, v in scores.items()}
    smoothed_scores = {k: sigmoid(10 * (v - 0.5)) for k, v in relative_positions.items()}
    min_smoothed = min(smoothed_scores.values())
    max_smoothed = max(smoothed_scores.values())
    return {k: 10 * (v - min_smoothed) / (max_smoothed - min_smoothed) for k, v in smoothed_scores.items()}
def verify_relative_relationships(original_scores, converted_scores, subcategory):
    for node1 in original_scores:
        for node2 in original_scores:
            if node1 != node2:
                original_diff = original_scores[node1] - original_scores[node2]
                converted_diff = converted_scores[node1] - converted_scores[node2]
                if (original_diff > 0 and converted_diff <= 0) or (original_diff < 0 and converted_diff >= 0):
                    print(f"\nVerifying relative relationships for {subcategory}")
                    print(f"Inconsistency found between {node1} and {node2}")
                    print(f"Original: {original_scores[node1]} vs {original_scores[node2]}")
                    print(f"Converted: {converted_scores[node1]} vs {converted_scores[node2]}")
def calculate_icc(df, subcat):
    df['A_str'] = df['A'].astype(str)
    df['B_str'] = df['B'].astype(str)
    df['Pair'] = df.apply(lambda x: '_'.join(sorted([x['A_str'], x['B_str']])), axis=1)
    df['Sign'] = df.apply(lambda x: 1 if x['A_str'] == min(x['A_str'], x['B_str']) else -1, axis=1)
    df['Score_Diff'] = (df['Review A Score'] - df['Review B Score']) * df['Sign']
    df['Comparison'] = (df['Comparison'].map(int) + 1) * df['Sign']
    icc_data = df[['Pair', 'Comparison', 'Score_Diff']]
    icc = pg.intraclass_corr(data=icc_data, targets='Pair', raters='Comparison', ratings='Score_Diff',
                             nan_policy='omit')
    icc['Subcategory'] = subcat
    return icc
def standardize_pairs(df):
    df['A_str'] = df['A'].astype(str)
    df['B_str'] = df['B'].astype(str)
    df['A_B'] = df.apply(lambda x: sorted([x['A_str'], x['B_str']]), axis=1)
    df['Pair'] = df['A_B'].apply(lambda x: '_'.join(x))
    df['Sign'] = df.apply(lambda x: 1 if x['A_str'] == x['A_B'][0] else -1, axis=1)
    df['Score_Diff'] = (df['Review A Score'] - df['Review B Score']) * df['Sign']
    return df
def build_comparison_matrix(df):
    paragraphs = pd.unique(df[['A_str', 'B_str']].values.ravel('K'))
    comparison_matrix = pd.DataFrame(0, index=paragraphs, columns=paragraphs, dtype=float)
    df_pairs = df.groupby(['A_str', 'B_str'])['Score_Diff'].mean().reset_index()
    for idx, row in df_pairs.iterrows():
        a = row['A_str']
        b = row['B_str']
        avg_score_diff = row['Score_Diff']
        comparison_matrix.loc[a, b] = avg_score_diff
    comparison_matrix = comparison_matrix.applymap(lambda x: np.sign(x))
    return comparison_matrix
def count_intransitive_triplets(matrix):
    paragraphs = matrix.index.tolist()
    triplets = list(combinations(paragraphs, 3))
    intransitive_count = 0
    total_triplets = len(triplets)
    for triplet in triplets:
        a, b, c = triplet
        ab = matrix.loc[a, b]
        bc = matrix.loc[b, c]
        ac = matrix.loc[a, c]
        if ab > 0 and bc > 0 and ac <= 0:
            intransitive_count += 1
        elif ab < 0 and bc < 0 and ac >= 0:
            intransitive_count += 1
        elif ab == 0 or bc == 0 or ac == 0:
            total_triplets -= 1
    return intransitive_count, total_triplets
df, Subcategorys = create_analysis_df()
df.to_csv('RawResult.csv')
results = defaultdict(lambda: defaultdict(dict))
for subcategory, group in df.groupby('Subcategory'):
    graph, nodes = build_graph(group)
    raw_scores = pagerank(graph, nodes)
    converted_scores = convert_to_0_10_scale(raw_scores)
    for node, score in converted_scores.items():
        paragraph, author = node.split('_')
        results[subcategory][paragraph][author] = score
output = []
for subcategory, paragraphs in results.items():
    for paragraph, authors in paragraphs.items():
        for author, score in authors.items():
            output.append({
                'Subcategory': subcategory,
                'Paragraph': paragraph,
                'Author': author,
                'Score': score
            })
output_df = pd.DataFrame(output)
output_df.to_csv('pagerank_results_balanced.csv', index=False)
print((output_df.groupby('Author').agg(sum).Score / 2.7).sort_values())
print("\nResults have been saved to 'pagerank_results_balanced.csv'")
for subcategory, group in df.groupby('Subcategory'):
    graph, nodes = build_graph(group)
    raw_scores = pagerank(graph, nodes)
    converted_scores = convert_to_0_10_scale(raw_scores)
    verify_relative_relationships(raw_scores, converted_scores, subcategory)
data = df.copy()
subcategories = data['Subcategory'].unique()
all_data = pd.DataFrame()
for subcat in subcategories:
    df_sub = data[data['Subcategory'] == subcat]
    df_sub['Mean Score'] = df_sub[['Review A Score', 'Review B Score']].mean(axis=1)
    df_sub['Diff Score'] = df_sub['Review A Score'] - df_sub['Review B Score']
    df_sub['Subcategory'] = subcat
    all_data = pd.concat([all_data, df_sub[['Subcategory', 'Mean Score', 'Diff Score']]])
all_data.to_csv('bland_altman_data.csv', index=False)
num_subcats = len(subcategories)
fig, axes = plt.subplots(nrows=(num_subcats + 1) // 3, ncols=3, figsize=(24, 6 * ((num_subcats + 1) // 3)))
axes = axes.flatten()
for idx, subcat in enumerate(subcategories):
    df_sub = all_data[all_data['Subcategory'] == subcat]
    mean_diff = df_sub['Diff Score'].mean()
    std_diff = df_sub['Diff Score'].std()
    ax = axes[idx]
    ax.scatter(df_sub['Mean Score'], df_sub['Diff Score'], alpha=0.5)
    ax.axhline(mean_diff, color='red', linestyle='--', label='Mean Difference')
    ax.axhline(mean_diff + 1.96 * std_diff, color='grey', linestyle='--', label='Limits of Agreement')
    ax.axhline(mean_diff - 1.96 * std_diff, color='grey', linestyle='--')
    ax.set_xlabel('Mean Score')
    ax.set_ylabel('Difference Score')
    ax.set_title(f'Bland-Altman Plot - {subcat}')
    ax.legend()
for i in range(idx + 1, len(axes)):
    fig.delaxes(axes[i])
plt.tight_layout()
plt.savefig('Bland-Altman.svg')
icc_results = []
transitivity_results = []
for subcat in subcategories:
    df_sub = data[data['Subcategory'] == subcat].copy()
    icc = calculate_icc(df_sub, subcat)
    icc_results.append(icc)
    df_sub = standardize_pairs(df_sub)
    comparison_matrix = build_comparison_matrix(df_sub)
    intransitive_count, total_triplets = count_intransitive_triplets(comparison_matrix)
    consistency_ratio = (total_triplets - intransitive_count) / total_triplets if total_triplets > 0 else None
    transitivity_results.append({
        'Subcategory': subcat,
        'Total_triplets': total_triplets,
        'Intransitive_triplets': intransitive_count,
        'Transitivity_consistency_ratio': consistency_ratio
    })
icc_all = pd.concat(icc_results, ignore_index=True)
icc_summary = icc_all[icc_all['Type'] == 'ICC2'][['Subcategory', 'ICC', 'CI95%']]
transitivity_df = pd.DataFrame(transitivity_results)
transitivity_df['Transitivity_consistency_ratio'] = transitivity_df['Transitivity_consistency_ratio'] * 100
merged_df = pd.merge(icc_summary, transitivity_df[['Subcategory', 'Transitivity_consistency_ratio']], on='Subcategory',
                     how='outer')
merged_df = merged_df[['Subcategory', 'ICC', 'CI95%', 'Transitivity_consistency_ratio']]
merged_df.rename(columns={
    'ICC': 'ICC (Intraclass Correlation Coefficient)',
    'CI95%': 'ICC 95% Confidence Interval',
    'Transitivity_consistency_ratio': 'Transitivity Consistency Ratio (%)'
}, inplace=True)
subcategory_order = {cat: i for i, cat in enumerate(subcategories)}
merged_df['subcategory_order'] = merged_df['Subcategory'].map(subcategory_order)
merged_df.sort_values('subcategory_order', inplace=True)
merged_df.drop('subcategory_order', axis=1, inplace=True)
merged_df = merged_df.reset_index(drop=True)
merged_df.to_csv('reliability_analysis.csv', index=False)
print("Combined Results:")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
print(merged_df)
print("\nResults have been saved to 'reliability_analysis.csv'")
