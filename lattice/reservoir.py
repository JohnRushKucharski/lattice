'''
Basic reservoir for storage nodes.

More complex reservoirs can be added by creating or importing
new class(es) that implements the Reservoir protocol.

For example, the canteen model can be used here.
'''

from typing import Protocol, Callable

type Output = tuple[float, float, tuple[float,...]]

class Reservoir(Protocol):
    '''
    A node that can store inflows.
    '''
    storage: float
    '''Current volume of stored inflows.'''
    capacity: float
    '''Maximum volume of stored inflows.'''

    @property
    def current_state(self) -> Output:
        '''Return current state of the reservoir, with same format as operate function outputs.'''

    def operate(self, inflow: float) -> Output:
        '''Operates reservoir, updates storage in place, and returns outputs.
        
        Returns:
            tuple[float, float, list[float]]: inflow, storage, [outflow_1, outflow_2, ...]
        '''
    def output_headers(self) -> tuple[str, str, tuple[str,...]]:
        '''Return output headers.'''

type Operations_Function = Callable[[Reservoir, float], Output]

def passive_operation(reservoir: Reservoir, inflow: float) -> Output:
    '''
    Passively operates a reservoir.
    
    Inflow, storage, outflows for the current timestep, and modifies storage in place.
    '''
    # only spilled releases
    release = max(0, reservoir.storage + inflow - reservoir.capacity)
    # stores all water until it reaches capacity (and spills)
    reservoir.storage = min(reservoir.capacity, reservoir.storage + inflow)
    return inflow, reservoir.storage, (release,)

passive_operation_headers: tuple[str, str, tuple[str,...]] = ('Inflow', 'Storage', ('Outflow',))
'''Return output headers.'''


class BasicReservoir(Reservoir):
    '''
    Simple reservoir model that stores inflows and releases them when its capacity is exceeded.
    '''
    def __init__(self, capacity: float = 1, initial_volume: float = 0,
                 operations: Operations_Function = passive_operation,
                 output_headers: tuple[str,...] = passive_operation_headers) -> None:
        self.capacity = capacity
        self.storage = initial_volume
        self.__operations = operations
        self.__output_headers = output_headers

    @property
    def current_state(self) -> Output:
        outflows = len(self.output_headers()[2])
        return (0, self.storage, tuple([0] * outflows))

    def operate(self, inflow: float) -> Output:
        return self.__operations(self, inflow)

    def output_headers(self) -> tuple[str, str, tuple[str,...]]:
        return self.__output_headers
