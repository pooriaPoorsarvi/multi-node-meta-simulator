from simulation_nodes import SimulationNode, MasterNode

import networkx as nx


class MultiNodeSimulation:
    """Configuration for the simulation environment comprised of multiple hardware simulators."""

    def __init__(self,
                 has_global_barrier: bool,
                 is_distributed: bool,
                 has_global_quanta: bool,
                 nodes: list[SimulationNode],
                 graph: nx.Graph,
                 master_node: MasterNode = None):
    
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


        if has_global_quanta:
            for node in self.nodes:
                id = node.get_id()
                min_latency_nano_seconds = min([self.graph[id][neighbor]['latency_nanoseconds'] for neighbor in self.graph.neighbors(id)])
                node.set_quanta_nanoseconds(min_latency_nano_seconds)
        if not self.is_distributed:
            assert master_node is not None, "In a non-distributed simulation, a master node must be provided."
            self.master_node = master_node

        
        # if has_global_barrier:
            # TODO: Implement global barrier management
            



    def simulate_network(self):
        """Get the total synchronization overhead in nanoseconds for all nodes."""
        for node in self.nodes:
            node.simulate_network()
    


        raise NotImplementedError("Global barrier and global quanta simulation not implemented yet.")

    def simulate_for_instructions(self, instructions: int):
        """Simulate the environment for a given number of instructions."""
        for node in self.nodes:
            node.target_instructions_goal = instructions

        return self.simulate()
    
    def simulate_for_nanoseconds_in_target(self, time_nanoseconds: int):
        """Simulate the environment for a given number of nanoseconds."""
        for node in self.nodes:
            node.target_time_nanoseconds_goal = time_nanoseconds

        return self.simulate()

    def schedule_nodes(self):
        if self.is_distributed:
            pass
        else:
            # TODO : use master node must be used here
            pass
    
    def pause_nodes_based_on_barrier(self):
        """Pause nodes based on the global barrier or neighbor synchronization. 
        If there is a global barrier, all nodes will wait (on host time) until ths slowest node has reached it's qunata.
        If there is no global barrier, each node will wait for the slowest neighbor to reach its quanta."""
        if self.has_global_barrier:
            max_host_time = 0
            finished = True
            for node in self.nodes:
                if node.current_host_time_nanoseconds > max_host_time:
                    max_host_time = node.current_host_time_nanoseconds
                if not node.is_done():
                    finished = False
            for node in self.nodes:
                node.jump_host_to_time(max_host_time)
            return finished
        else:
            finished = True
            for node in self.nodes:
                if not node.is_done():
                    finished = False
                id = node.get_id()
                neighbors = self.graph.neighbors(id)
                max_neighbor_time = node.current_host_time_nanoseconds
                for neighbor in neighbors:
                    neighbor_node = self.nodes_dict[neighbor]
                    if neighbor_node.current_host_time_nanoseconds > max_neighbor_time:
                        max_neighbor_time = neighbor_node.current_host_time_nanoseconds
                node.jump_host_to_time(max_neighbor_time)
            return finished



    def simulate(self):
        self.schedule_nodes()
        finished = False
        while not finished:
            for node in self.nodes:
                if not node.is_done():
                    node.simulate_for_quanta()
            finished = self.pause_nodes_based_on_barrier()
        time = max([node.current_host_time_nanoseconds for node in self.nodes])
        return time
                            
                    
                            
        
                



