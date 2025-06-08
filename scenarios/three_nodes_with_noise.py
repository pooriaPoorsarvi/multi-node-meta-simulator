from simulation_nodes import SimpleQemuSimulationNodeWithNoiseWithPreDetermainedNoise, MasterNode
from multi_node import MultiNodeSimulation 
from networkx import Graph

import random
size = 10_0000
array1_noise = [random.uniform(-0.3, 0.3) for _ in range(size)] 
array2_noise = [random.uniform(-0.3, 0.3) for _ in range(size)] 
array3_noise = [random.uniform(-0.3, 0.3) for _ in range(size)] 

def get_simulation(has_global_barrier: bool = True):

    node1 = SimpleQemuSimulationNodeWithNoiseWithPreDetermainedNoise(
        noise_array=array1_noise,
        simulation_speed_ips=5e8,
        id= "Node1",
        manages_quanta=False,
    )

    node2 = SimpleQemuSimulationNodeWithNoiseWithPreDetermainedNoise(
        noise_array=array2_noise,
        simulation_speed_ips=5e8,
        id= "Node2",
        manages_quanta=False,
    )
    
    node3 = SimpleQemuSimulationNodeWithNoiseWithPreDetermainedNoise(
        noise_array=array3_noise,
        simulation_speed_ips=5e8,
        id= "Node3",
        manages_quanta=False,
    )

    graph = Graph()
    graph.add_edge(node1.get_id(), node2.get_id(), latency_nanoseconds=int(1000))
    graph.add_edge(node2.get_id(), node3.get_id(), latency_nanoseconds=int(1000))

    master_node = MasterNode()  # No master node in this scenario

    multi_node_simulation = MultiNodeSimulation(
        has_global_barrier= has_global_barrier,
        is_distributed=False,
        has_global_quanta=True,
        nodes=[node1, node2, node3],
        graph=graph,
        master_node=master_node,
        verbose=False,
    )

    return multi_node_simulation


target_time_ns = int(1e9)
print("global barrier enabled:")
time = get_simulation().simulate_for_nanoseconds_in_target(target_time_ns)
print(f"Simulation time: {time*1e-9} seconds for {target_time_ns} nanoseconds in target time.")

print("*"*50)
print("*"*50)
print("*"*50)

print("global barrier disabled:")
time = get_simulation(has_global_barrier=False).simulate_for_nanoseconds_in_target(target_time_ns)
print(f"Simulation time: {time*1e-9} seconds for {target_time_ns} nanoseconds in target time.")