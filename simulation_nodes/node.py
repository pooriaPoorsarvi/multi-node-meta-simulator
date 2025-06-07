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
        """Calculate the nanoseconds to simulate one quanta."""
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
        super().__init__(*args, **kwargs)

    def jump_host_to_time(self, time_nanoseconds: int):
        """Jump to a specific time in nanoseconds."""
        self.current_host_time_nanoseconds = time_nanoseconds

    def synchronization_overhead_in_nanoseconds(self):
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
    def simulate_for_quanta(self):
        """Run the simulation node."""
        assert self.quanta_nanoseconds > 0, "Quanta nanoseconds must be set before simulating."
        self.current_host_time_nanoseconds += self.target_quanta_nanoseconds_to_host_nanoseconds()
        self.current_host_time_nanoseconds += self.get_synchronization_communication_overhead()
        self.current_host_time_nanoseconds += self.synchronization_overhead_in_nanoseconds()
        self.current_target_time_nanoseconds += self.get_quanta_nanoseconds()
        self.target_instructions_executed += self.get_instructions_per_quanta()

        return self.current_host_time_nanoseconds

    def get_number_of_quanta_for_nanoseconds_in_target(self, time_nanoseconds: int):
        """Get the number of quanta for a given time in nanoseconds."""
        return time_nanoseconds // self.get_quanta_nanoseconds()
    
    def get_number_of_quanta_for_instructions(self, instructions: int):
        """Get the number of quanta for a given number of instructions."""
        return instructions // self.get_instructions_per_quanta()

    def simulate_for_instructions(self, instructions: int):
        """Run the simulation node for a given number of instructions."""
        self.target_instructions_goal = instructions
        while not self.is_done():
            yield self.simulate_for_quanta()

    def simulate_for_nanoseconds_in_target(self, time_nanoseconds: int):
        """Run the simulation node for a given time in nanoseconds."""
        self.target_time_nanoseconds_goal = time_nanoseconds
        while not self.is_done():
            yield self.simulate_for_quanta()

class MasterNode:
    pass