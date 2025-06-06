from .node import SimulationNode


class SimpleQemuSimulationNode(SimulationNode):
    
    def synchronization_overhead_in_nanoseconds(self):
        """Get the synchronization overhead in nanoseconds."""
        # For QEMU, we assume a fixed overhead for synchronization
        return 1000
