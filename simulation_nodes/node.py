from typing import Self
import math

class SimulationNode:

    def get_simulation_speed_ips(self):
        """Get the simulation speed in instructions per second."""
        return self.simulation_speed_ips

    def get_machine_cycle_per_nano_second(self):
        """Get the number of machine cycles per nanosecond."""
        return self.machine_cycle_per_nano_second
    
    def get_machine_instruction_per_cycle(self):
        """Get the number of machine instructions per cycle."""
        return self.machine_instruction_per_cycle
    
    def get_machine_instruction_per_nano_second(self):
        """Get the number of machine instructions per nanosecond."""
        return self.get_machine_cycle_per_nano_second() * self.get_machine_instruction_per_cycle()
    
    def get_quanta_nanoseconds(self):
        """Get the duration of a quanta in nanoseconds."""
        assert self.quanta_nanoseconds > 0, "Quanta nanoseconds must be set before getting it."
        return self.quanta_nanoseconds

    def get_instructions_per_quanta(self):
        """Get the number of instructions per quanta."""
        return self.get_machine_instruction_per_nano_second() * self.get_quanta_nanoseconds()
        

    def target_nano_to_host_nano(self):
        """Calculate the host nano seconds it takes to simulate one target nano second."""

        host_second_to_simulate_target_nano = self.get_machine_instruction_per_nano_second() / self.get_simulation_speed_ips()

        return math.ceil(host_second_to_simulate_target_nano * 1e9) # Convert to nanoseconds

    def target_quanta_nanoseconds_to_host_nanoseconds(self):
        """Calculate the nanoseconds to simulate one quanta, based on host time."""
        return self.target_nano_to_host_nano() * self.get_quanta_nanoseconds()

    def get_id(self):
        """Get the ID of the simulation node."""
        return self.name
    
    def get_synchronization_communication_overhead(self):
        """Get the synchronization communication overhead in nanoseconds."""
        return self.synchronization_communication_overhead
    
    def connect_node(self, node: Self):
        """Connect this node to another simulation node."""
        self.connected_nodes.add(node)


    def __init__(self,
                 *args,
                 simulation_speed_ips: int,
                 id: str,
                 manages_quanta: bool,
                 **kwargs
                 ):
        """Initialize the simulation node.
        Args:
            simulation_speed_ips (int): The speed of the simulation in instructions per second.
        """
        self.name = id
        self.simulation_speed_ips = simulation_speed_ips
        self.quanta_nanoseconds = -1
        self.current_host_time_nanoseconds = 0
        self.current_target_time_nanoseconds = 0
        self.target_instructions_executed = 0
        self.target_instructions_goal = -1
        self.target_time_nanoseconds_goal = -1

        self.machine_cycle_per_nano_second = 5 # Default value, can be overridden by subclasses, 2 GhZ
        self.machine_instruction_per_cycle = 2
        self.manages_quanta = manages_quanta
        self.connected_nodes = set()
        self.synchronization_communication_overhead = 0
        self.quanta_communication_overhead = 0
        self.at_barrier = False
        self.can_process_barrier = False

        # information that enable partrial quanta simulation
        self.next_marker_time_ns = 0
        self.current_indp_executed = 0
        self.next_quanta_instructions_executed = 0
        self.next_synchronization_communication_overhead = 0
        self.next_synchronization_overhead_in_nanoseconds = 0


        # Because of none global quanta, we need to calculate the next quanta information after initialization.
        self.has_been_initialized = False
        super().__init__(*args, **kwargs)


    def initialize(self):
        """Initialize the simulation node."""
        assert self.quanta_nanoseconds > 0, "Quanta nanoseconds must be set before initializing the node."
        self.calculate_next_quanta_information()
        self.has_been_initialized = True


    def get_synchronization_overhead_in_nanoseconds(self):
        """Get the synchronization overhead in nanoseconds."""
        return 0
    
    def set_quanta_nanoseconds(self, quanta_nanoseconds: int):
        """Set the quanta duration in nanoseconds."""
        assert quanta_nanoseconds > 0, "Quanta nanoseconds must be greater than zero."
        self.quanta_nanoseconds = quanta_nanoseconds
    
    def simulate_network(self):
        """set any communication overheads based on network state."""
        self.synchronization_communication_overhead = 0

    def is_done(self):
        """Check if the simulation node has reached its goal."""
        if self.target_instructions_goal > 0:
            return self.target_instructions_executed >= self.target_instructions_goal
        elif self.target_time_nanoseconds_goal > 0:
            return self.current_target_time_nanoseconds >= self.target_time_nanoseconds_goal
        else:
            return False
        
    def calculate_next_quanta_information(self):
        assert self.current_indp_executed == 0, "Can not estimate next execution, mid execution"
        
        # How much will the next quanta take in host nanoseconds?
        self.next_marker_time_ns = self.target_quanta_nanoseconds_to_host_nanoseconds()

        # How many instruction will be executed in the next quanta?
        self.next_quanta_instructions_executed = self.get_instructions_per_quanta()
        

        
        
        return self.next_marker_time_ns

    def calculate_barrier_end_information(self):
        """Calculate the information needed to move past the barrier."""
        assert self.at_barrier, "Can not calculate barrier end information if not at barrier."
        assert self.current_indp_executed == 0, "Can not calculate barrier end information if current executed is not 0."


        # At the barrier how much communication overhead will be there?
        self.next_synchronization_communication_overhead = self.get_synchronization_communication_overhead()
        
        # How much overhead will be at the barrier for everything else?
        self.next_synchronization_overhead_in_nanoseconds = self.get_synchronization_overhead_in_nanoseconds()

        over_heads = self.next_synchronization_communication_overhead + self.next_synchronization_overhead_in_nanoseconds
        self.next_marker_time_ns = over_heads
        
        
    
    def get_next_indp_work_time_ns_host(self):
        """Get the remaining host time in the current quanta."""
        return self.next_marker_time_ns - self.current_indp_executed




    def move_within_quanta(self):
        """Move within the current quanta, simulating the given amount of time."""

        # TODO : in the middle of quanta the instruction and target time are not updated right now.

        if self.current_indp_executed >= self.next_marker_time_ns:
            assert self.current_indp_executed == self.next_marker_time_ns, "Host execution in this quanta should be equal to the host length of next quanta."
            
            # We are at the barrier
            self.at_barrier = True

            # We have reached the end of the quanta.
            # Update the target time and instructions executed.
            # This one calls the function cause the quanta is constant, if it was not constant, we would need to save it like the other variables.
            self.current_target_time_nanoseconds += self.get_quanta_nanoseconds()
            self.target_instructions_executed += self.next_quanta_instructions_executed

            # Rest and calculate the barrier computation information.
            self.current_indp_executed = 0
            self.calculate_barrier_end_information()



    def move_with_in_barrier(self):
        """Move within the barrier, simulating the given amount of time."""

        if self.current_indp_executed >= self.next_marker_time_ns:

            # Update the flags for the barrier.
            self.at_barrier = False
            self.can_process_barrier = False

            # Rest and calcuate the next quanta information.
            self.current_indp_executed = 0
            self.calculate_next_quanta_information()

    def is_independent(self) -> bool:
        """Check if the node is independent, meaning it can work without waiting for other nodes."""
        if self.is_done():
            return False
        if self.at_barrier and not self.can_process_barrier:
            return False
        return True
        

    def simulate(self, amount_time_to_simulate_ns: int):
        """Run the simulation node for a specific amount of time.
        If host_simulation_time_nanoseconds is -1, it will move ahead until we reach the quanta."""
        assert self.has_been_initialized, "Node must be initialized before simulating." 
        
        if self.is_independent():
            remaining_host_quanta_time = self.get_next_indp_work_time_ns_host()

            assert remaining_host_quanta_time >= amount_time_to_simulate_ns, f"Can not simulate {amount_time_to_simulate_ns} ns, remaining host quanta time is {remaining_host_quanta_time} ns."
            self.current_indp_executed += amount_time_to_simulate_ns

        # Other wise it's fine and we are just waiting

        # update global host time
        self.current_host_time_nanoseconds += amount_time_to_simulate_ns
        # update how much host has gone forward for quanta
        
        if self.at_barrier:
            # We are processing the barrier
            if self.can_process_barrier:
                self.move_with_in_barrier()
            # Else it's just waisted time like real life

        else:
            self.move_within_quanta()


class MasterNode:
    pass