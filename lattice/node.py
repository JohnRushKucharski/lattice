'''
System node types. 

Nodes are the basic building blocks of the system,
they are the smallest unit of computation used to build up the system.

Edges are the connections between nodes, 
these connections are built-up using a sort of publisher-subscriber model.
Nodes "subscribe" to upstream node(s) and upstream nodes "publish" outflows.

All nodes are publishers (send flows downstream) intermediate and outlet nodes 
are also subscribers (receive flows from other nodes). 
'''
from enum import Enum
from dataclasses import dataclass, field
from typing import Protocol, Self, Callable, Any, runtime_checkable

import pandas as pd

#from lattice.reservoir import Reservoir, BasicReservoir
from canteen.reservoir import Reservoir, BasicReservoir

class Tag(str, Enum):
    '''
    Node tags are used to categorize nodes in the system.
    '''
    INFLOW = 'inflow'
    '''Upstream most node, can create new inflows.'''

    # Intermediate nodes: accept inflow from other nodes and produce outflows
    STORAGE = 'storage'
    '''Stores inflows.'''
    DIVERSION = 'diversion'
    '''Divert inflows out of system.'''
    RESCALE = 'rescale'
    '''Aggregate or rescale inflows.'''
    PERFORMANCE = 'performance'
    '''Compute performance metrics from inflows.'''
    OUTLET = 'outlet'
    '''Downstream most node (from which all flows leave the system).'''

#TODO: add implementation for DIVERSION, RESCALE, and PERFORMANCE nodes.

@dataclass
class Log:
    '''
    Stores node data for log entries.
    '''
    records: list[Any] = field(default_factory=list)
    '''Simulation data.'''
    headers: tuple[str] = field(default_factory=tuple)

    def logger(self, function: Callable[..., Any]) -> Callable[..., float]:
        '''
        Decorator to log node level simulation outputs and send node outflows.
        '''
        def wrapper(*args, **kwargs) -> float:
            output = function(*args, **kwargs)
            self.records.append(output)
            return output
        return wrapper

    def to_dataframe(self) -> pd.DataFrame:
        '''Return log data as a pandas DataFrame.'''
        return pd.DataFrame(self.records, columns=self.headers)

@runtime_checkable
class Node(Protocol):
    '''
    A node in the system (all nodes are publishers/senders).
    '''
    tag: Tag
    '''Node tag.'''
    name: str
    '''Node name.'''

    def receive(self) -> float:
        '''Return inflows from upstream senders.'''

    def send(self) -> float:
        '''Return flow to send to downstream receivers.'''
    def senders(self) -> set[Self]:
        '''Return upstream nodes.'''

class Subscriber(Protocol):
    '''
    A node that can receive inflows from other nodes.
    '''
    def add_sender(self, sender: Node) -> None:
        '''Add node that sends flow to this node.'''
    def remove_sender(self, sender: Node) -> None:
        '''Remove node that sends flow to this node.'''

def transfer_flow(node: Node) -> float:
    '''
    Transfer flow from upstream sender to downstream receiver.
    Default send method for input, and outlet nodes.
    '''
    return node.receive()

class Inflow: # Implements Node interface.
    '''
    Upstream most node, can create new inflows.
    
    Implments Node interface.
    '''
    def __init__(self, input_data: list[float],
                 name: str = '', starting_position: int = 0,
                 operations: Callable[[Node],float] = transfer_flow,
                 loop: bool = False) -> None:
        self.tag = Tag.INFLOW
        self.data = input_data
        self.name = name if name else self.tag.value
        self.__timestep = starting_position - 1
        self.__operations = operations
        self.__loop = loop

    def attach_log(self, log: Log) -> Log:
        '''Modifies operations to include logging. Returns log headers.'''
        self.__operations = log.logger(self.__operations)
        log.headers = ('Inflow',)
        return log

    def receive(self) -> float:
        if (self.__timestep + 1 == len(self.data)
            and self.__loop):
            self.reset()
        self.__timestep += 1
        return self.data[self.__timestep]

    def send(self) -> float:
        return self.__operations(self)
    def senders(self) -> set[Node]:
        return set()

    def reset(self) -> None:
        '''Reset node starting position for inflow to first timestep in data.'''
        self.__timestep = -1

class Storage: # Implements Node, Subscriber interfaces
    '''
    Node that can store inflows.
    
    Implements Node and Subscriber interfaces.
    '''
    def __init__(self, reservoir: Reservoir = BasicReservoir(),
                 name: str = '', senders: None|set[Node] = None) -> None:
        self.tag = Tag.STORAGE
        self.reservoir = reservoir
        self.name = name if name else self.tag.value
        self.__senders = senders if senders else set()
        self.__operations = reservoir.operations

    def attach_log(self, log: Log) -> Log:
        '''Modifies operations to include logging.'''
        self.__operations = log.logger(self.__operations)
        log.records.append(self.reservoir.current_state)
        log.headers = self.reservoir.output_headers()
        return log

    @property
    def volume(self) -> float:
        '''Return current stored volume at the node.'''
        return self.reservoir.storage

    def receive(self) -> float:
        return sum(sender.send() for sender in self.senders())

    def send(self) -> float:
        inflows = self.receive()
        operation_outputs = self.__operations(inflows)
        # sum together all releases
        return sum(operation_outputs[2])
    def senders(self) -> set[Node]:
        return self.__senders
    def add_sender(self, sender: Node) -> None:
        self.__senders.add(sender)
    def remove_sender(self, sender: Node) -> None:
        self.__senders.remove(sender)

    def reset(self, storage: float) -> None:
        '''
        Reset storage to a new initial condition.
        '''
        self.reservoir.storage = storage

class Outlet(Node, Subscriber):
    '''Node that sends flow out of the system.'''
    def __init__(self, name: str = '',
                 senders: None|set[Node] = None) -> None:
        self.tag = Tag.OUTLET
        self.name = name if name else self.tag.value
        self.__senders = senders if senders else set()
        self.__operations = transfer_flow

    def attach_log(self, log: Log) -> Log:
        '''Modifies operations to include logging.'''
        self.__operations = log.logger(self.__operations)
        log.headers = ('Outflow',)
        return log

    def receive(self) -> float:
        # needs to only be inflows in .send() call.
        return sum(sender.send() for sender in self.senders())

    def send(self) -> float:
        return self.__operations(self)
    def senders(self) -> set[Node]:
        return self.__senders
    def add_sender(self, sender: Node) -> None:
        self.__senders.add(sender)
    def remove_sender(self, sender: Node) -> None:
        self.__senders.remove(sender)
