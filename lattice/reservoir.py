'''
Basic reservoir for storage nodes.

More complex reservoirs can be added by creating or importing
new class(es) that implements the Reservoir protocol.

For example, the canteen model can be used here.
'''

from typing import Protocol, Callable

class Reservoir(Protocol):
    '''
    A node that can store inflows.
    '''
    storage: float
    '''Current volume of stored inflows.'''
    capacity: float
    '''Maximum volume of stored inflows.'''

    def operate(self, inflow: float) -> tuple[float, float, list[float]]:
        '''Operates reservoir, updates storage in place, and returns outputs.
        
        Returns:
            tuple[float, float, list[float]]: inflow, storage, [outflow_1, outflow_2, ...]
        '''

type Operations_Function = Callable[[Reservoir, float], tuple[float, float, list[float]]]

def passive_operations(reservoir: Reservoir, inflow: float) -> tuple[float, float, list[float]]:
    '''
    Passively operates a reservoir.
    
    Inflow, storage, outflows for the current timestep, and modifies storage in place.
    '''
    # only spilled releases
    release = max(0, reservoir.storage + inflow - reservoir.capacity)
    # stores all water until it reaches capacity (and spills)
    reservoir.storage = min(reservoir.capacity, reservoir.storage + inflow)
    return inflow, reservoir.storage, [release]

class BasicReservoir(Reservoir):
    '''
    Simple reservoir model that stores inflows and releases them when its capacity is exceeded.
    '''
    def __init__(self, capacity: float = 1, initial_volume: float = 0,
                 operations: Operations_Function = passive_operations) -> None:
        self.capacity = capacity
        self.storage = initial_volume
        self.__operations = operations

    def operate(self, inflow: float) -> tuple[float, float, list[float]]:
        return self.__operations(self, inflow)
