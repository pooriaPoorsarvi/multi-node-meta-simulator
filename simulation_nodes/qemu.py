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

        noise_factor = random.uniform(-0.1, 0.05)  
        without_noise = super().target_quanta_nanoseconds_to_host_nanoseconds()
        return int(without_noise * (1 + noise_factor))  # Add noise to the base time





