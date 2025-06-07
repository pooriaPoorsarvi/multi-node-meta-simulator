from .node import SimulationNode
import random


class SimpleQemuSimulationNode(SimulationNode):
    
    def get_synchronization_overhead_in_nanoseconds(self):
        """Get the synchronization overhead in nanoseconds."""
        # For QEMU, we assume a fixed overhead for synchronization
        return 1000


class SimpleQemuSimulationNodeWithNoise(SimpleQemuSimulationNode):
    
    def target_quanta_nanoseconds_to_host_nanoseconds(self):
        """Calculate the nanoseconds to simulate one quanta, based on host time, with noise."""
        # Adding a random noise factor to the simulation speed

        noise_factor = random.uniform(-0.05, 0.1)  
        without_noise = super().target_quanta_nanoseconds_to_host_nanoseconds()
        return int(without_noise * (1 + noise_factor))  # Add noise to the base time

class SimpleQemuSimulationNodeWithNoiseWithPreDetermainedNoise(SimpleQemuSimulationNode):

    def __init__(self, *args, noise_array: list[float], **kwargs):
        """Initialize the node with a predetermined noise array."""
        super().__init__(*args, **kwargs)
        self.noise_array = noise_array
        self.noise_index = 0

    def target_quanta_nanoseconds_to_host_nanoseconds(self):
        """Calculate the nanoseconds to simulate one quanta, based on host time, with noise."""
        # Adding a random noise factor to the simulation speed

        without_noise = super().target_quanta_nanoseconds_to_host_nanoseconds()
        noise_factor = self.noise_array[self.noise_index]
        self.noise_index += 1
        return int(without_noise * (1 + noise_factor))  # Add noise to the base time





