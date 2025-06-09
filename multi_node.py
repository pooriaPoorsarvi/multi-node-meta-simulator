import sys

from simulation_nodes import SimulationNode, MasterNode

import networkx as nx
from loguru import logger

class MultiNodeSimulation:
    """Configuration for the simulation environment comprised of multiple hardware simulators."""

    def __init__(self,
                 has_global_barrier: bool,
                 is_distributed: bool,
                 has_global_quanta: bool,
                 nodes: list[SimulationNode],
                 graph: nx.Graph,
                 master_node: MasterNode = None,
                 global_quanta_nanoseconds: int = -1,
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

        # TODO The next part, setting quanta is wrong I think, should remove 
        for edge in graph.edges:
            node1, node2 = edge
            latency_nanoseconds = graph[node1][node2]['latency_nanoseconds']
            self.nodes_dict[node1].connect_node(self.nodes_dict[node2])
            self.nodes_dict[node1].set_quanta_nanoseconds(latency_nanoseconds)
            self.nodes_dict[node2].connect_node(self.nodes_dict[node1])
            self.nodes_dict[node2].set_quanta_nanoseconds(latency_nanoseconds)


        if not has_global_quanta:
            for node in self.nodes:
                id = node.get_id()
                min_latency_nano_seconds = min([self.graph[id][neighbor]['latency_nanoseconds'] for neighbor in self.graph.neighbors(id)])
                node.set_quanta_nanoseconds(min_latency_nano_seconds)
        else:
            assert global_quanta_nanoseconds > 0, "Global quanta nanoseconds must be greater than 0."
            for node in self.nodes:
                node.set_quanta_nanoseconds(global_quanta_nanoseconds)


        if not self.is_distributed:
            assert master_node is not None, "In a non-distributed simulation, a master node must be provided."
            self.master_node = master_node

        for node in self.nodes:
            node.initialize()

        self.verbose = verbose
        self.setup_logger()
        
        # if has_global_barrier:
            # TODO: Implement global barrier management
            




        # raise NotImplementedError("Global barrier and global quanta simulation not implemented yet.")

    def setup_logger(self):
        # TODO probably need to move logger setup to a separate module
        # 1) remove the default handler
        logger.remove()

        # 2) define a filter that only lets DEBUG-level records through if verbose=True
        def filter_verbose(record):
            level_no = record["level"].no
            is_debug = level_no == logger.level("DEBUG").no
            return self.verbose or not is_debug

        # 3) add a sink with that filter
        logger.add(
            sys.stderr,
            level="DEBUG",           # allow DEBUG records… 
            filter=filter_verbose,   # …but drop them if verbose==False
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "{message}"
            ),
            backtrace=True,
            diagnose=True,
        )


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
        return all(node.MODE == "SYNCHRONIZATION" or node.MODE == "WAITING_ON_BARRIER" for node in self.nodes)

    def is_local_barrier_ready(self, node: SimulationNode):
        can_leave_barrier = True

        for neighbor in self.graph.neighbors(node.get_id()):
            neighbor_node = self.nodes_dict[neighbor]
            if neighbor_node.MODE == "QUANTA_SIMULATION":
                if neighbor_node.current_target_time_nanoseconds <= node.current_target_time_nanoseconds:
                    can_leave_barrier = False
                    break
        
        return can_leave_barrier

    def update_barriers(self):
        """Update whether or not a nod can leave its end of quanta barrier"""
        if len(self.nodes) == 1:
            if self.nodes[0].MODE == "WAITING_ON_BARRIER":
                self.nodes[0].change_mode("SYNCHRONIZATION")
        elif self.has_global_barrier:
            # If we have a global barrier, we check if all nodes have reached their quanta.
            if self.is_glbal_barrier_ready():
                for node in self.nodes:
                    node.change_mode("SYNCHRONIZATION")
        else:
            for node in self.nodes:
                if self.is_local_barrier_ready(node) and node.MODE == "WAITING_ON_BARRIER" and not node.is_done():
                    node.change_mode("SYNCHRONIZATION")
                    
                

        

    def print_simulation_state(self):
        """Print the current state of the simulation."""
        if self.verbose:
            for node in self.nodes:
                total_execution_time = "NA"
                time_left = "NA"
                if node.execution_details is not None:
                    total_execution_time = node.execution_details.get_total_execution_time()
                    time_left = node.execution_details.get_time_left_ns()
                logger.debug(f"Node {node.get_id()} - "
                    f"Mode: {node.MODE}, "
                    f"Current Host Time: {node.current_host_time_nanoseconds} ns, "
                    f"Target Time: {node.current_target_time_nanoseconds} ns, "
                    f"current target instruction executed: {node.target_instructions_executed}, "
                    f"Execution total execution time: {total_execution_time}"
                    f"Execution detail time left: {time_left} ns, ")


    def simulate(self):
        self.schedule_nodes()

        finished = False
        while not finished:
            finished = True
            min_time_to_simulate = min([node.execution_details.get_time_left_ns() for node in self.nodes if (not node.MODE == "WAITING_ON_BARRIER")])
            
            logger.debug("="*50)
            self.print_simulation_state()
            logger.debug(f"Simulating for {min_time_to_simulate} nanoseconds.")
            
            assert min_time_to_simulate > 0, "Nodes are not finished yet, but no time to simulate. This should not happen."
         
            for node in self.nodes:
                node.simulate(min_time_to_simulate)
                if not node.is_done():
                    finished = False

            logger.debug("after simulating")
            self.print_simulation_state()

            self.update_barriers()
            
            logger.debug("after updating barriers")
            self.print_simulation_state()
            logger.debug("="*50)

           
                

        
        time = max([node.current_host_time_nanoseconds for node in self.nodes])
        return time
                            
                    
                            
        
                



