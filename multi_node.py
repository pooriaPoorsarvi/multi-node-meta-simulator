from simulation_nodes import SimulationNode

import networkx as nx


class MultiNodeSimulation:
    """Configuration for the simulation environment comprised of multiple hardware simulators."""

    def __init__(self,
                 has_global_barrier: bool,
                 is_distributed: bool,
                 has_global_quanta: bool,
                 nodes: list[SimulationNode],
                 graph: nx.Graph):
    
        """        Initialize the simulation configuration.

        Args:
            has_global_barrier (bool): Whether the simulation has a global barrier. if false will only pause nodes based on their virtual clock and the clock of the nodes its connected to.
            is_distributed (bool): Whether the simulation is distributed across multiple nodes. If false, the simulation will be managed via one master node and multiple worker nodes.
            has_global_quanta (bool): Whether the simulation has global quanta. if false, the quanta on each component will be managed based on its connections to other nodes.
        """
        self.has_global_barrier = has_global_barrier
        self.is_distributed = is_distributed
        self.has_global_quanta = has_global_quanta
        self.current_time_nanoseconds = 0
        self.nodes = nodes

        if not is_distributed:
            for node in nodes:
                assert not node.manages_quanta, "In a non-distributed simulation, nodes should not manage their own quanta."

        

        set_ids = set()
        for node in self.nodes:
            assert node.get_id() not in set_ids, f"Node ID {node.get_id()} is not unique."
            set_ids.add(node.get_id())

        self.graph = graph
        self.nodes_dict = {node.get_id(): node for node in nodes}
        for edge in graph.edges:
            node1, node2 = edge
            latency_nanoseconds = graph[node1][node2]['latency_nanoseconds']
            self.nodes_dict[node1].connect_node(self.nodes_dict[node2])
            self.nodes_dict[node1].set_quanta_nanoseconds(latency_nanoseconds)
            self.nodes_dict[node2].connect_node(self.nodes_dict[node1])
            self.nodes_dict[node2].set_quanta_nanoseconds(latency_nanoseconds)


        # if has_global_quanta:
            # TODO: Implement global quanta management
        
        # if has_global_barrier:
            # TODO: Implement global barrier management
            



    def simulate_network(self):
        """Get the total synchronization overhead in nanoseconds for all nodes."""
        for node in self.nodes:
            node.simulate_network()
    

    def simulate(self, simulators_time_generator, number_of_quantas):

        max_time = 0

        if self.has_global_barrier:
            if self.has_global_quanta:
                if not self.is_distributed:
                    assert len(set(number_of_quantas)) == 1, "All nodes must have the same number of quanta in a global quanta simulation."
                    quantas = number_of_quantas[0]
                    print(f"Running global quanta simulation for {quantas} quantas.")
                    for _ in range(quantas):
                        # If there is a global barrier, we need to wait for all nodes to finish their simulation
                        max_time = max([next(simulator_time) for simulator_time in simulators_time_generator])
                        for node in self.nodes:
                            node.jump_to_time(max_time)
                    return max_time

        raise NotImplementedError("Global barrier and global quanta simulation not implemented yet.")

    def simulate_for_instructions(self, instructions: int):
        """Simulate the environment for a given number of instructions."""
        simulators_time_generator = [node.simulate_for_instructions(instructions) for node in self.nodes]
        number_of_quantas = list([node.get_number_of_quanta_for_instructions(instructions) for node in self.nodes])

        return self.simulate(simulators_time_generator, number_of_quantas)
    
    def simulate_for_nanoseconds_in_target(self, time_nanoseconds: int):
        """Simulate the environment for a given number of nanoseconds."""
        simulators_time_generator = [node.simulate_for_nanoseconds_in_target(time_nanoseconds) for node in self.nodes]
        number_of_quantas = list([node.get_number_of_quanta_for_nanoseconds_in_target(time_nanoseconds) for node in self.nodes])

        return self.simulate(simulators_time_generator, number_of_quantas)


        
        
                



