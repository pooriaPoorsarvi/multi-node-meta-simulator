from simulation_nodes import SimpleQemuSimulationNode
from multi_node import MultiNodeSimulation
from networkx import Graph


def get_simulation():

    node1 = SimpleQemuSimulationNode(
        simulation_speed_ips=5e6,
        id= "Node1",
        manages_quanta=False,
    )

    node2 = SimpleQemuSimulationNode(
        simulation_speed_ips=5e6,
        id= "Node2",
        manages_quanta=False,
    )

    graph = Graph()
    graph.add_edge(node1.get_id(), node2.get_id(), latency_nanoseconds=500)

    multi_node_simulation = MultiNodeSimulation(
        has_global_barrier= True,
        is_distributed=False,
        has_global_quanta=True,
        nodes=[node1, node2],
        graph=graph
    )

    return multi_node_simulation

instruction_count = int(1e10)  # 10 billion instructions
time = get_simulation().simulate_for_instructions(int(instruction_count))
print(f"Simulation time: {time*1e-9} seconds for {instruction_count} instructions.")

target_time = int(10e9)  # 1 second in nanoseconds
time = get_simulation().simulate_for_nanoseconds_in_target(target_time)
print(f"Simulation time: {time*1e-9} seconds for {target_time} nanoseconds in target time.")