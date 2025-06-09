from .node import SimulationNode


class SimpleGem5SimulationNodeWithImportableNoise(SimulationNode):

    def __init__(self, 
                 noise_array: list[float],
                 synchronization_overhead_percentage: float = -1,
                 synchronization_overhead_ns: int = -1,
                 *args, **kwargs):
        """Initialize the node with a predetermined noise array."""
        super().__init__(*args, **kwargs)
        self.noise_array = noise_array
        self.noise_index = 0
        self.synchronization_overhead_percentage = synchronization_overhead_percentage
        self.synchronization_overhead_ns = synchronization_overhead_ns
    
    def target_quanta_nanoseconds_to_host_nanoseconds(self):
        """Calculate the nanoseconds to simulate one quanta, based on host time, with noise."""
        # Adding a random noise factor to the simulation speed

        without_noise = super().target_quanta_nanoseconds_to_host_nanoseconds()
        noise_factor = self.noise_array[self.noise_index]
        self.noise_index += 1
        if self.noise_index >= len(self.noise_array):
            self.noise_index = 0
        return int(without_noise * (1 + noise_factor))

    def get_synchronization_overhead_in_nanoseconds(self):
        """Get the synchronization overhead in nanoseconds."""
        if self.synchronization_overhead_percentage >= 0:
            without_noise_quanta_execution = super().target_quanta_nanoseconds_to_host_nanoseconds()
            return int(without_noise_quanta_execution * self.synchronization_overhead_percentage)
        elif self.synchronization_overhead_ns > 0:
            return self.synchronization_overhead_ns
        else:
            raise ValueError("Either synchronization_overhead_percentage or synchronization_overhead_ns must be set.")







