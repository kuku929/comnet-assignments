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
    return tab
try:
    tab = pd.read_csv("sim.csv")
except:
    tab = construct_data()
finally:
    tab = tab.set_index(['n', 'L'])
    # let's plot the probability of success
    # wide_tab = tab.pivot(index="L", columns="n", values="success_rate")
    # plots success rate with L for various n
    # sns.relplot(data=tab, x="L", y="success_rate", hue="n", kind="line")
    # plots spread of success rate with n
    # shows very less deviation
    # sns.relplot(data=tab,x="n", y="success_rate", kind="line")
    n = 3
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
    # plots the different success rate for 10 nodes
    # as L is increased. As L increases the variation
    # of successes increases but the mean remains the same
    sns.boxplot(data=one_n, y="node_success_rate", x="L") 
    one_node_data = one_n.loc[one_n['name'] == 'node_0']
    sns.relplot(data=one_node_data,x="L", y="node_success_rate", kind="line", hue="name")
    # show how the success rate of a node changes
    # as more nodes are added to the system
    plt.xticks(rotation=90)
    plt.show()
