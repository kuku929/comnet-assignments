import random
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import ast


def simulate_exponential_backoff(n_nodes=10, L=5, simulation_time=10000):
    MAX_STAGE = 7
    nodes = []

    for _ in range(n_nodes):
        stage = 0
        backoff = random.randint(1, 2**(4 + stage))
        nodes.append({'stage': stage, 'counter': backoff, 'tx': 0, 'success': 0, 'collisions': 0})

    slot = 0
    tx_remaining = 0  # how many slots the current transmission still lasts
    total_collisions = 0
    total_successes = 0

    while slot < simulation_time:
        transmitting_nodes = []

        if tx_remaining > 0:
            tx_remaining -= 1
            slot += 1
            continue

        # Decrement backoff for all eligible nodes
        for node in nodes:
            if node['counter'] > 0:
                node['counter'] -= 1

        # Identify which nodes are transmitting now
        for idx, node in enumerate(nodes):
            if node['counter'] == 0:
                transmitting_nodes.append(idx)

        if len(transmitting_nodes) == 0:
            slot += 1
            continue

        # At least one node is transmitting
        for idx in transmitting_nodes:
            nodes[idx]['tx'] += 1

        if len(transmitting_nodes) == 1:
            # Success
            total_successes += 1
            nodes[transmitting_nodes[0]]['success'] += 1
            nodes[transmitting_nodes[0]]['stage'] = 0
            nodes[transmitting_nodes[0]]['counter'] = random.randint(1, 2**(4))
        else:
            # Collision
            total_collisions += 1
            for idx in transmitting_nodes:
                nodes[idx]['collisions'] += 1
                nodes[idx]['stage'] = min(nodes[idx]['stage'] + 1, MAX_STAGE)
                new_backoff = random.randint(1, 2**(4 + nodes[idx]['stage']))
                nodes[idx]['counter'] = new_backoff

        # Transmission takes L slots
        tx_remaining = L - 1
        slot += 1

    total_attempts = sum(node['tx'] for node in nodes)
    total_success = sum(node['success'] for node in nodes)
    total_collision = sum(node['collisions'] for node in nodes)

    throughput = total_success * L / simulation_time  # fraction of time slots used successfully

    return {
        'total_attempts': total_attempts,
        'total_successes': total_success,
        'total_collisions': total_collision,
        'collision_rate': total_collision / total_attempts if total_attempts else 0,
        'success_rate': total_success / total_attempts if total_attempts else 0,
        'throughput': throughput,
        'per_node': [{'tx': n['tx'], 'success': n['success'], 'collisions': n['collisions']} for n in nodes]
    }

def construct_data():
    res = {'n':[], 'L':[],'total_attempts':[], 'total_successes':[], 
        'total_collisions':[],  'collision_rate':[], 
        'success_rate':[], 'throughput':[], 'per_node':[]}
    for n in range(1, 11):
        for L in range(1, 101):
            ret = simulate_exponential_backoff(n, L)
            res['n'].append(n)
            res['L'].append(L)
            for key in ret.keys():
                res[key].append(ret[key])
    
    tab = pd.DataFrame(data=res, columns=['n','L','total_attempts', 'total_successes', 'total_collisions', 'collision_rate', 'success_rate', 'throughput', 'per_node']) 
    tab.to_csv("sim.csv")
    res = {'n':[], 'L':[],'total_attempts':[], 'total_successes':[], 
        'total_collisions':[],  'collision_rate':[], 
        'success_rate':[], 'throughput':[], 'per_node':[]}
    for n in range(20, 50, 10):
        for L in range(1, 101):
            ret = simulate_exponential_backoff(n, L)
            res['n'].append(n)
            res['L'].append(L)
            for key in ret.keys():
                res[key].append(ret[key])
    
    tab1 = pd.DataFrame(data=res, columns=['n','L','total_attempts', 'total_successes', 'total_collisions', 'collision_rate', 'success_rate', 'throughput', 'per_node']) 
    tab1.to_csv("bigsim.csv")
    return tab

def vs_n_plots(tab: pd.DataFrame):
    # Create a single figure for all throughput plots
    # plt.figure(figsize=(10, 6))
    # print(tab.head())
    # Plot throughput for different L values
    # for L in [1, 5, 10, 15, 20, 40, 60, 80, 100]:
    #     subset = tab.loc[(slice(None), L), :].reset_index()
    #     sns.lineplot(data=subset, x='n', y='throughput', label=f'L={L}' if L in [1, 5, 10, 15, 20, 40, 60, 80, 100] else None)
    req = [1, 5, 10, 15, 20, 40, 60, 80, 100]
    filtered = tab.loc[tab['L'].isin(req)]
    sns.relplot(data=filtered,x="n", y="throughput", hue="L", kind="line")
    # Plot average throughput across all L values
    # avg_throughput = tab.groupby('n')['throughput'].mean().reset_index()
    # sns.lineplot(data=avg_throughput, x='n', y='throughput', label='Average for L from 1 to 100', linewidth=3, color='black')

    plt.title('Throughput vs Number of Nodes')
    plt.xlabel('Number of Nodes (n)')
    plt.ylabel('Throughput')
    # plt.legend(title='L values', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # Create a single figure for all collision rate plots
    # plt.figure(figsize=(10, 6))

    # # Plot collision rate for different L values
    # for L in [1, 20, 40, 60, 80, 100]:
    #     subset = tab.loc[(slice(None), L), :].reset_index()
    #     sns.lineplot(data=subset, x='n', y='collision_rate', label=f'L={L}' if L in [1, 20, 40, 60, 80, 100] else None)

    # # Plot average collision rate across all L values
    # avg_collision = tab.groupby('n')['collision_rate'].mean().reset_index()
    # sns.lineplot(data=avg_collision, x='n', y='collision_rate', label='Average for L from 1 to 100', linewidth=3, color='black')
    req = [1, 20, 40, 60, 80, 100]
    filtered = tab.loc[tab['L'].isin(req)]
    sns.relplot(data=filtered,x="n", y="collision_rate", hue="L", kind="line")

    plt.title('Collision Rate vs Number of Nodes')
    plt.xlabel('Number of Nodes (n)')
    plt.ylabel('Collision Rate')
    # plt.legend(title='L values', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    plt.show()

def vs_L_plots(tab: pd.DataFrame):
    # Create a single figure for all throughput plots
    # plt.figure(figsize=(10, 6))

    # Plot throughput for different n values
    # for n in range(1,11):
    #     subset = tab.loc[tab['n']==n].reset_index()
    #     sns.lineplot(data=subset, x='L', y='throughput', label=f'n={n}')
    sns.relplot(data=tab,x="L", y="throughput", hue="n", kind="line")
    # Plot average throughput across all n values
    # avg_throughput = tab.groupby('L')['throughput'].mean().reset_index()
    # sns.lineplot(data=avg_throughput, x='L', y='throughput', label='Average for n from 1 to 10', linewidth=3, color='black')

    plt.title('Throughput vs Transmission length')
    plt.xlabel('Transmission length L')
    plt.ylabel('Throughput')
    # plt.legend(title='n values', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # Create a single figure for all collision rate plots
    # plt.figure(figsize=(10, 6))

    # # Plot collision rate for different n values
    # for n in range(1,11):
    #     subset = tab.loc[(n, slice(None)), :].reset_index()
    #     sns.lineplot(data=subset, x='L', y='collision_rate', label=f'n={n}')

    sns.relplot(data=tab,x="L", y="collision_rate", hue="n", kind="line")
    
    # # Plot average collision rate across all n values
    # avg_collision = tab.groupby('L')['collision_rate'].mean().reset_index()
    # sns.lineplot(data=avg_collision, x='L', y='collision_rate', label='Average for n from 1 to 10', linewidth=3, color='black')

    plt.title('Collision Rate vs Transmission length')
    plt.xlabel('Transmission length L')
    plt.ylabel('Collision Rate')
    # plt.legend(title='n values', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    plt.show()

# Plot the plots
try:
    tab = pd.read_csv("sim.csv")
except:
    tab = construct_data()
finally:
    vs_n_plots(tab)
    vs_L_plots(tab)

    # # let's plot the probability of success
    # wide_tab = tab.pivot(index="L", columns="n", values="success_rate")
    # # plots success rate with L for various n
    # sns.relplot(data=tab, x="L", y="success_rate", hue="n", kind="line")
    # # plots spread of success rate with n
    # # shows very less deviation
    # sns.relplot(data=tab,x="n", y="success_rate", hue="L", kind="line")
    tab = pd.read_csv("bigsim.csv")
    tab = tab.set_index(['n', 'L'])
    print(tab.head())
    n = 30
    one_n = tab.loc[n]
    dataframes = []
    for L in range(1,101):
        res = {'L':[], 'name': [], 'tx': [], 'success': [], 'collisions': []} 
        ls = ast.literal_eval(one_n.loc[L]['per_node'])
        for node, row in enumerate(ls):
            for key in row.keys():
                res[key].append(row[key])
            res['name'].append('node_'+str(node))
            res['L'].append(L)
        dataframes.append(pd.DataFrame(data=res))
    # this is the dataset for each node 
    # for a range of L
    acc = pd.concat(dataframes)
    one_n = pd.merge(one_n, acc, on='L', how='left')
    one_n['node_success_rate'] = one_n['success']/one_n['tx']
    req = [1, 5, 10, 15, 20, 40, 60, 80, 100]
    req = [i for i in range(1, 101)]
    one_n = one_n.loc[one_n['L'].isin(req)]
    mean_arr = []
    for L in req:
        mean_arr.append(one_n.loc[one_n['L'] == L]['node_success_rate'].mean())
    for L, mean in zip(req, mean_arr):
        one_n.loc[one_n['L'] == L, 'node_success_rate']/=mean
    # plots the different success rate for 10 nodes
    # as L is increased. As L increases the variation
    # of successes increases but the mean remains the same
    sns.boxplot(data=one_n, y="node_success_rate", x="L", hue="L") 
    # one_node_data = one_n.loc[one_n['name'] == 'node_0']
    # sns.relplot(data=one_node_data,x="L", y="node_success_rate", kind="line", hue="name")
    # # show how the success rate of a node changes
    # # as more nodes are added to the system
    plt.xticks(rotation=90)
    plt.show()
