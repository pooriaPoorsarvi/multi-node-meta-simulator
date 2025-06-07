from typing import Self, Literal
import math

class ExecutionDetails:
    """Base class for execution details of a simulation node for a each mode."""
    time_executed_ns: int = 0

    def __init__(self):
        """Initialize the execution details."""
        self.time_executed_ns = 0

    def get_total_execution_time(self) -> int:
        raise NotImplementedError("This method should be implemented in subclasses.")

    def get_time_left_ns(self) -> int:
        """Get the time left for the execution."""
        return self.get_total_execution_time() - self.time_executed_ns

class QuantaExecution(ExecutionDetails):
    """Data class to hold the execution information of a quanta."""
    host_length_to_execute_ns: int
    instructions_executed: int

    def __init__(self, host_length_to_execute_ns: int, instructions_executed: int):
        """Initialize the quanta execution details."""
        self.host_length_to_execute_ns = host_length_to_execute_ns
        self.instructions_executed = instructions_executed
        super().__init__()
    

    def get_total_execution_time(self) -> int:
        """Get the total execution time for the quanta."""
        return self.host_length_to_execute_ns

class BarrierExecution(ExecutionDetails):
    """Data class to hold the execution information of a barrier."""
    communication_overhead_ns: int
    synchronization_overhead_ns: int

    def __init__(self, communication_overhead_ns: int, synchronization_overhead_ns: int):
        """Initialize the barrier execution details."""
        self.communication_overhead_ns = communication_overhead_ns
        self.synchronization_overhead_ns = synchronization_overhead_ns
        super().__init__()

    def get_total_execution_time(self) -> int:
        """Get the total execution time for the barrier."""
        return self.communication_overhead_ns + self.synchronization_overhead_ns



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
        return 0
    
    def connect_node(self, node: Self):
        """Connect this node to another simulation node."""
        self.connected_nodes.add(node)

    def get_synchronization_overhead_in_nanoseconds(self):
            """Get the synchronization overhead in nanoseconds."""
            return 0
    def set_quanta_nanoseconds(self, quanta_nanoseconds: int):
            """Set the quanta duration in nanoseconds."""
            assert quanta_nanoseconds > 0, "Quanta nanoseconds must be greater than zero."
            self.quanta_nanoseconds = quanta_nanoseconds

    def is_done(self):
        """Check if the simulation node has reached its goal."""
        if self.target_instructions_goal > 0:
            return self.target_instructions_executed >= self.target_instructions_goal
        elif self.target_time_nanoseconds_goal > 0:
            return self.current_target_time_nanoseconds >= self.target_time_nanoseconds_goal
        else:
            return False

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

        self.MODE: Literal['QUANTA_SIMULATION', 'WAITING_ON_BARRIER', 'SYNCHRONIZATION'] = 'QUANTA_SIMULATION'
        self.execution_details: ExecutionDetails = None


        # Because of none global quanta, we need to calculate the next quanta information after initialization.
        self.has_been_initialized = False
        super().__init__(*args, **kwargs)

    
    def initialize(self):
        """Initialize the simulation node."""
        assert self.quanta_nanoseconds > 0, "Quanta nanoseconds must be set before initializing the node."
        self.change_mode('QUANTA_SIMULATION')

        # self.calculate_next_quanta_information()
        self.has_been_initialized = True

    def change_mode(self, MODE: Literal['QUANTA_SIMULATION', 'WAITING_ON_BARRIER', 'SYNCHRONIZATION']):
        
        self.MODE = MODE
        if self.MODE == 'QUANTA_SIMULATION':
            self.execution_details = QuantaExecution(
                host_length_to_execute_ns=self.target_quanta_nanoseconds_to_host_nanoseconds(),
                instructions_executed=self.get_instructions_per_quanta()
            )

        elif self.MODE == 'WAITING_ON_BARRIER':
            self.execution_details = None

        elif self.MODE == 'SYNCHRONIZATION':
            self.execution_details = BarrierExecution(
                communication_overhead_ns=self.get_synchronization_communication_overhead(),
                synchronization_overhead_ns=self.get_synchronization_overhead_in_nanoseconds()
            )
        
        
    

    def continue_quanta_simulation(self):
        """Move within the current quanta, simulating the given amount of time."""

        # TODO : in the middle of quanta the instruction and target time are not updated right now.

        if self.execution_details.get_time_left_ns() <= 0:
            assert self.execution_details.get_time_left_ns() == 0

            old_execution_details: QuantaExecution = self.execution_details
            

            # We have reached the end of the quanta.
            # Update the target time and instructions executed.
            # This one calls the function cause the quanta is constant, if it was not constant, we would need to save it like the other variables.
            self.current_target_time_nanoseconds += self.get_quanta_nanoseconds()
            
            self.target_instructions_executed += old_execution_details.instructions_executed

            self.change_mode('WAITING_ON_BARRIER')



    def continue_sync(self):
        """Move within the barrier, simulating the given amount of time."""

        if self.execution_details.get_time_left_ns() <= 0:

            # Change mode.
            self.change_mode('QUANTA_SIMULATION')
      

    def simulate(self, amount_time_to_simulate_ns: int):
        """Run the simulation node for a specific amount of time.
        If host_simulation_time_nanoseconds is -1, it will move ahead until we reach the quanta."""
        assert self.has_been_initialized, "Node must be initialized before simulating." 
        
        if not self.execution_details is None:
            remaining_host_quanta_time = self.execution_details.get_time_left_ns()

            assert remaining_host_quanta_time >= amount_time_to_simulate_ns, f"Can not simulate {amount_time_to_simulate_ns} ns, remaining host quanta time is {remaining_host_quanta_time} ns."
            self.execution_details.time_executed_ns += amount_time_to_simulate_ns


        # update global host time
        self.current_host_time_nanoseconds += amount_time_to_simulate_ns
        
        if self.MODE == 'SYNCHRONIZATION':
            self.continue_sync()

        elif self.MODE == 'QUANTA_SIMULATION':
            self.continue_quanta_simulation()
        
        # Else it's just waisted time like real life


class MasterNode:
    pass