
from networkx import Graph

from simulation_nodes import SimpleGem5SimulationNodeWithImportableNoise
from multi_node import MultiNodeSimulation, MasterNode
import random
import seaborn as sns
import matplotlib.pyplot as plt


GEM5_IPS = 250_000
FINAL_TARGET_TIME_NS = int(1e6)  

def get_pair_wise_network(
        has_global_barrier: bool,
        has_global_quanta: bool,
        is_distributed: bool,
        n_nodes: int,
        ips_per_node: int,
        communication_latency_ns,
        synchronization_overhead_percentage: float = -1,
        synchronization_overhead_ns: int = -1,
    ):
    """Create a pairwise network for the simulation."""
    
    noise_arrays = [
        [
            random.uniform(-0.3, 0) for _ in range(1000)
        ] for _ in range(n_nodes)
    ]
    
    nodes = [
        SimpleGem5SimulationNodeWithImportableNoise(
            noise_array=noise_arrays[i],
            simulation_speed_ips=ips_per_node,
            id= f"Node{i}",
            manages_quanta=is_distributed,
            synchronization_overhead_percentage=synchronization_overhead_percentage,
            synchronization_overhead_ns=synchronization_overhead_ns
        ) for i in range(n_nodes)
    ]

    graph = Graph()
    if n_nodes >= 2:
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                graph.add_edge(
                    nodes[i].get_id(),
                    nodes[j].get_id(),
                    latency_nanoseconds=int(communication_latency_ns)
                )
    master_node = MasterNode()  # No master node in this scenario

    multi_node_simulation = MultiNodeSimulation(
        has_global_barrier= has_global_barrier,
        is_distributed=is_distributed,
        has_global_quanta=has_global_quanta,
        nodes=nodes,
        graph=graph,
        master_node=master_node,
        verbose=False,
        global_quanta_nanoseconds=communication_latency_ns
    )

    return multi_node_simulation


def gem5_net(
        num_nodes,
        communication_latency_ns: int
    ):
   
    return get_pair_wise_network(
        has_global_barrier=True,
        has_global_quanta=True,
        is_distributed=False,
        n_nodes=num_nodes,
        # This assumes that we are simulating a 64 core system, so based on simulation nodes IPS gets divided by 64
        synchronization_overhead_ns=int((num_nodes ** 2) * 5e3),
        ips_per_node=GEM5_IPS/(4), # running 4 nodes per core, so divide by 4
        communication_latency_ns=communication_latency_ns,
    )



def test_nodes():
    node_results = []
    for i in range(7):
        num_nodes = 2 ** i
        print(f"Running simulation with {num_nodes} nodes...")
        net: MultiNodeSimulation = gem5_net(
            num_nodes,
            communication_latency_ns=500
        )
        host_time = net.simulate_for_nanoseconds_in_target(FINAL_TARGET_TIME_NS)
        print(f"Simulation time: {host_time * 1e-9} seconds for {FINAL_TARGET_TIME_NS} nanoseconds in target time.")
        print("="*50)
        node_results.append(host_time * 1e-9)
    # Save plot normalized to the first result
    run_times_normalized = [time / node_results[0] for time in node_results]
    print("Run Times Normalized:", run_times_normalized)
    print("Number of Nodes:", [2 ** i for i in range(7)])
    # Save seaborn lineplot with number of nodes on x-axis and normalized time on y-axis
    sns.set_theme(style="whitegrid")
    ax = sns.lineplot(
        x=[2 ** i for i in range(7)],
        y=run_times_normalized,
        marker='o'
    )
    ax.set(xlabel='Number of Nodes', ylabel='Normalized Time (to 2 nodes)')
    ax.set_title("Simulation Time vs Number of Nodes (Normalized)")
    # Save figure
    ax.figure.savefig("gem5_simulation_time_vs_num_nodes.png")
    # Clear the current figure to avoid overlap in future plots
    plt.clf()

def test_latencies():
    # Now focus on 64 nodes with various communication latencies
    communication_latencies = [(2 ** i) * 500 for i in range(9)]
    communication_results = []
    for communication_latency_ns in communication_latencies:
        print(f"Running simulation with 64 nodes and communication latency {communication_latency_ns} ns...")
        net: MultiNodeSimulation = gem5_net(
            num_nodes=64,
            communication_latency_ns=communication_latency_ns
        )
        host_time = net.simulate_for_nanoseconds_in_target(FINAL_TARGET_TIME_NS)
        print(f"Simulation time: {host_time * 1e-9} seconds for {FINAL_TARGET_TIME_NS} nanoseconds in target time.")
        print("="*50)
        communication_results.append(host_time * 1e-9)

    # Save plot normalized to the first result
    communication_results_normalized = [time / communication_results[0] for time in communication_results]
    print("Communication Results Normalized:", communication_results_normalized)
    print("Communication Latencies:", communication_latencies)
    
    # Save seaborn plot using barplot with communication latencies on x-axis and normalized time on y-axis
    sns.set_theme(style="whitegrid")
    ax = sns.barplot(
        x=[int(c/1000) if int(c/1000) > 0 else c/1000 for c in communication_latencies ],
        y=communication_results_normalized
    )
    ax.set(xlabel='Communication Latency (μs)', ylabel='Normalized Time (to 500 ns)')
    # TODO bad trick to fix the x-axis formatting, fix later
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x)}' if x >= 1 else f'0.5'))
    ax.set_title("Simulation Time vs Communication Latency (Normalized)")
    # Save figure
    ax.figure.savefig("gem5_simulation_time_vs_communication_latency.png")
    # Clear the current figure to avoid overlap in future plots
    plt.clf()


if __name__ == "__main__":

    test_nodes()
    test_latencies()


    
    
    







    




