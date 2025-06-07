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
                 master_node: MasterNode = None,
                 verbose: bool = False):
    
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

        for node in self.nodes:
            node.initialize()

        self.verbose = verbose
        
        # if has_global_barrier:
            # TODO: Implement global barrier management
            




        # raise NotImplementedError("Global barrier and global quanta simulation not implemented yet.")

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
    def is_glbal_barrier_ready(self):
        """Check if the global barrier is ready."""
        return all(node.at_barrier for node in self.nodes)

    def is_local_barrier_ready(self, node: SimulationNode):
        return all(self.nodes_dict[neighbor].at_barrier for neighbor in self.graph.neighbors(node.get_id()))

    def update_barriers(self):
        """Update whether or not a nod can leave its end of quanta barrier"""
        if self.has_global_barrier:
            # If we have a global barrier, we check if all nodes have reached their quanta.
            if self.is_glbal_barrier_ready():
                for node in self.nodes:
                    node.can_process_barrier = True
        else:
            is_global_barrier_ready = self.is_glbal_barrier_ready()
            for node in self.nodes:
                if self.is_local_barrier_ready(node) and node.at_barrier and not node.is_done():
                    node.can_process_barrier = True
                    # if not is_global_barrier_ready:
                    #     print(f"Node {node.get_id()} can process barrier, but global barrier is not ready.")
                

        

    def print_simulation_state(self):
        """Print the current state of the simulation."""
        for node in self.nodes:
            print(f"Node {node.get_id()} - "
                  f"At Barrier: {node.at_barrier}, "
                  f"Can Process Barrier: {node.can_process_barrier}, "
                  f"Current Host Time: {node.current_host_time_nanoseconds} ns, "
                  f"Target Time: {node.current_target_time_nanoseconds} ns, "
                  f"Current Executed: {node.current_indp_executed} ns, "
                  f"Next Marker Time: {node.next_marker_time_ns} ns, "
                  f"current target instruction executed: {node.target_instructions_executed}, ")


    def simulate(self):
        self.schedule_nodes()

        finished = False
        while not finished:
            finished = True
            min_time_to_simulate = min([node.get_next_indp_work_time_ns_host() for node in self.nodes if node.is_independent()])
            if self.verbose:
                print("="*50)
                self.print_simulation_state()
                print(f"Simulating for {min_time_to_simulate} nanoseconds.")
            assert min_time_to_simulate > 0, "Nodes are not finished yet, but no time to simulate. This should not happen."
         
            for node in self.nodes:
                node.simulate(min_time_to_simulate)
                if not node.is_done():
                    finished = False

            if self.verbose:
                print("after simulating")
                self.print_simulation_state()

            self.update_barriers()
            
            if self.verbose:
                print("after updating barriers")
                self.print_simulation_state()
                print("="*50)

           
                

        
        time = max([node.current_host_time_nanoseconds for node in self.nodes])
        return time
                            
                    
                            
        
                



