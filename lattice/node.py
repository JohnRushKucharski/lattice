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
from canteen.reservoir import Reservoir, BasicReservoir, Operations

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
    headers: tuple[str,...] = field(default_factory=tuple)

    def logger(self, function: Callable[..., Any]) -> Callable[..., float]:
        '''
        Decorator to log node level simulation outputs and send node outflows.
        '''
        def wrapper(*args, **kwargs) -> float:
            output = function(*args, **kwargs)
            self.records.append(output)
            return output
        return wrapper

    def records_by_label(self, label: str) -> list[float|tuple[float,...]]:
        '''Return log data by label.'''        
        try:
            index = self.headers.index(label)
            return [record[index] for record in self.records]
        except ValueError as e:
            if label == 'outflow':
                return [record[-1] for record in self.records]
            if label == 'inflow':
                return [record[0] for record in self.records]
            for header in self.headers:
                if isinstance(header, tuple) and label in header:
                    index = header.index(label)
                    return [record[index] for record in self.records]
            raise e

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

@dataclass
class Transfer:
    '''
    Transfer flow from upstream sender to downstream receiver.
    
    Implements the Operations interface of the Canteen library.
    '''
    transform_fn: Callable[[float], float] = lambda x: x
    '''Transform inflow to outflow.'''

    def operate(self, inflow: float) -> tuple[float, float]:
        '''Transfer inflow to outflow.'''
        return inflow, self.transform_fn(inflow)
    def output_labels(self) -> tuple[str, str]:
        '''Return output labels.'''
        return ('inflow', 'outflow')

# def transfer_flow(node: Node) -> float:
#     '''
#     Transfer flow from upstream sender to downstream receiver.
#     Default send method for input, and outlet nodes.
#     '''
#     return node.receive()

@dataclass
class Inflow:
    '''
    Upstream most node, creates system inflow.
    Implements Node, Iterator interfaces.
    
    Note: for stochastic inflows, use a generator function to create inflow data.
    '''
    tag: Tag = Tag.INFLOW
    '''Node tag.'''
    name: str = ''
    '''Node name. Set to tag value if not provided.'''
    data: list[float] = field(default_factory=list)
    '''Inflow data.'''
    operations: None|Operations = None
    '''Node operations. Default Transfer by default.'''

    def __post_init__(self):
        if not self.name:
            self.name = self.tag.value
        if not self.operations:
            self.operations = Transfer()
        self.__timestep = -1
        self.__loop = False

    def __key(self) -> tuple:
        return (self.tag, self.name, tuple(self.data), type(self.operations))
    def __hash__(self) -> int:
        return hash(self.__key())
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Inflow):
            return False
        return self.__key() == other.__key()
    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    @property
    def loop(self) -> bool:
        '''Return loop status.'''
        return self.__loop
    @loop.setter
    def loop(self, value: bool) -> None:
        '''
        Set loop status.
        
        If True, returns to first data element after last timestep.
        False raises StopIteration after last timestep. False by default.
        '''
        self.__loop = value
    def reset(self) -> None:
        '''Reset node starting position to first timestep in data.'''
        self.__timestep = -1

    def __iter__(self):
        return self
    def __next__(self):
        stop = len(self.data)
        if self.__timestep + 1 == stop:
            if self.__loop:
                self.reset()
            else:
                raise StopIteration
        self.__timestep += 1
        return self.data[self.__timestep]

    def attach_log(self, log: Log) -> Log:
        '''
        Wraps operations.operate function with log.
        '''
        self.operations.operate = log.logger(self.operations.operate)
        log.headers = self.operations.output_labels()
        return log

    def receive(self) -> float:
        '''Return inflow at current timestep.'''
        return self.__next__() #pylint: disable=unnecessary-dunder-call

    def send(self) -> float:
        '''Return outflow to downstream receivers.'''
        inflow = self.receive()
        return self.operations.operate(inflow)[1]
    def senders(self) -> set[Node]:
        '''Return empty set for inflow node since it has no upstream senders.'''
        return set()

# class Inflow: # Implements Node interface.
#     '''
#     Upstream most node, can create new inflows.

#     Implments Node interface.
#     '''
#     def __init__(self, input_data: list[float],
#                  name: str = '', starting_position: int = 0,
#                  operations: Callable[[Node],float] = transfer_flow,
#                  loop: bool = False) -> None:
#         self.tag = Tag.INFLOW
#         self.data = input_data
#         self.name = name if name else self.tag.value
#         self.operations = operations
#         self.__timestep = starting_position - 1
#         self.__loop = loop

#     def __iter__(self):
#         return self
#     def __next__(self):
#         stop = len(self.data)
#         if self.__timestep + 1 == stop:
#             if self.__loop:
#                 self.reset()
#             else:
#                 raise StopIteration
#         self.__timestep += 1
#         return self.data[self.__timestep]

#     def attach_log(self, log: Log) -> Log:
#         '''Modifies operations to include logging. Returns log headers.'''
#         self.operations = log.logger(self.operations)
#         log.headers = ('Inflow',)
#         return log

#     def receive(self) -> float:
#         '''
#         Returns inflow at current timestep, and increments timestep to next inflow.
#         '''
#         return self.__next__()

#     def send(self) -> float:
#         '''
#         Sends inflow to downstream nodes.

#         Follows rules of operations function,
#         transfer_flow collects inflow and transfers it as outflow by default.
#         '''
#         return self.operations(self)
#     def senders(self) -> set[Node]:
#         '''Return empty set for inflow node since it has not upstream senders.'''
#         return set()

#     def reset(self) -> None:
#         '''Reset node starting position for inflow to first timestep in data.'''
#         self.__timestep = -1

@dataclass
class Storage:
    '''Node that can store inflows.
    Implements Node, Subscriber, Hashable interfaces.
    
    Note:
        [1] Mutable storage, senders properties are excluded from hash.
            i.e., 2 nodes with different storage volumes and senders are considered equal.
    '''
    tag = Tag.STORAGE
    '''Node tag.'''	
    name: str = ''
    '''Node name. Defaults to tag value if not provided.'''
    reservoir: None | Reservoir = None
    '''Reservoir object. Defaults to BasicReservoir if not provided.'''
    __senders: set[Node] = field(default_factory=set)
    '''Upstream nodes that send flow to this node.'''

    def __post_init__(self):
        if not self.name:
            self.name = self.tag.value
        if not self.reservoir:
            self.reservoir = BasicReservoir()
        def operate(inflow: float) -> tuple[float, float, tuple[float]]:
            '''Wrapper for reservoir operations.'''
            output = self.reservoir.operations.operate(self.reservoir, inflow)
            output = output if isinstance(output, tuple) else (output,)
            return (inflow, self.reservoir.storage, output)
        self.operate = operate

    def __key(self) -> tuple:
        return (self.tag, self.name,
                self.reservoir.name,
                self.reservoir.capacity, #note: mutable storage propery excluded.
                type(self.reservoir.operations))
    def __hash__(self) -> int:
        return hash(self.__key())
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Storage):
            return False
        return self.__key() == other.__key()
    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def attach_log(self, log: Log) -> Log:
        '''Modifies operations to include logging.'''
        self.operate = log.logger(self.operate)
        log.headers = tuple(['inflow', 'storage'] + list(self.reservoir.operations.output_labels()))
        return log

    def receive(self) -> float:
        '''Return inflows from upstream senders.'''
        return sum(sender.send() for sender in self.senders())
    def send(self) -> float:
        '''
        Return outflows to downstream receivers.
        
        Calls receive method to get inflows from upstream senders,
        then calls operations method to transform inflows to outflows.
        '''
        inflows = self.receive()
        outputs = self.operate(inflows)
        return sum(outputs[2])
    def senders(self) -> set[Node]:
        '''Return set of upstream nodes providing inflows.'''
        return self.__senders
    def add_sender(self, sender: Node) -> None:
        '''Add node that sends flow to this node (through receive method).'''
        self.__senders.add(sender)
    def remove_sender(self, sender: Node) -> None:
        '''Removes node that sends flow to this node.'''
        self.__senders.remove(sender)
    def reset(self, storage: float) -> None:
        '''
        Reset storage to a new initial condition.
        '''
        self.reservoir.storage = storage

# class Storage: # Implements Node, Subscriber interfaces
#     '''
#     Node that can store inflows.

#     Implements Node and Subscriber interfaces.
#     '''
#     def __init__(self, reservoir: None | Reservoir = None,
#                  name: str = '', senders: None|set[Node] = None) -> None:
#         self.tag = Tag.STORAGE
#         self.name = name if name else self.tag.value
#         self.__senders = senders if senders else set()
#         self.reservoir = reservoir if reservoir else BasicReservoir()
#         def operate(inflow: float) -> tuple[float, float, tuple[float]]:
#             '''Wrapper for reservoir operations.'''
#             output = self.reservoir.operations(self.reservoir, inflow)
#             output = output if isinstance(output, tuple) else (output,)
#             return (inflow, self.reservoir.storage, output)
#         self.operations = operate

#     def attach_log(self, log: Log) -> Log:
#         '''Modifies operations to include logging.'''
#         #self.__operations = log.logger(self.__operations)
#         self.operations = log.logger(self.operations)
#         #log.records.append(self.reservoir.current_state)
#         #log.headers = self.reservoir.output_headers()
#         return log

#     @property
#     def volume(self) -> float:
#         '''Return current stored volume at the node.'''
#         return self.reservoir.storage

#     def receive(self) -> float:
#         '''Return inflows from upstream senders.'''
#         rcvd = sum(sender.send() for sender in self.senders())
#         return rcvd
#         #return sum(sender.send() for sender in self.senders())

#     def send(self) -> float:
#         '''
#         Return outflows to downstream receivers.

#         Calls recieve method to get inflows from upstream senders,
#         then calls operations method to transform inflows to outflows.
#         '''
#         inflows = self.receive()
#         # TODO: Needs a copy of reservoir in operations I think.
#         operation_outputs = self.operations(inflows)
#         # sum together all releases
#         # TODO: this expects (inflow, storage, release) tuple - which is not what is returned.
#         return sum(operation_outputs[2])
#     def senders(self) -> set[Node]:
#         '''Return set of upstream nodes providing inflows.'''
#         return self.__senders
#     def add_sender(self, sender: Node) -> None:
#         '''Add node that sends flow to this node (through recieve method).'''
#         self.__senders.add(sender)
#     def remove_sender(self, sender: Node) -> None:
#         '''Removes node that sends flow to this node.'''
#         self.__senders.remove(sender)

#     def reset(self, storage: float) -> None:
#         '''
#         Reset storage to a new initial condition.
#         '''
#         self.reservoir.storage = storage

@dataclass
class Outlet(Node, Subscriber):
    '''
    Node that sends flow out of the system.
    Implements Node, Subscriber, Hashable interfaces.
    
    Note:
        [1] Mutable senders property is excluded from hash.
            i.e., 2 nodes with different senders are considered equal.
    '''
    tag: Tag = Tag.OUTLET
    '''Node tag.'''
    name: str = ''
    '''Node name.'''
    operations: None|Operations = None
    '''Node operations. Default Transfer by default.'''
    __senders: set[Node] = field(default_factory=set)
    '''Upstream nodes that send flow to this node.'''

    def __post_init__(self):
        if not self.name:
            self.name = self.tag.value
        if not self.operations:
            self.operations = Transfer()

    # def __init__(self, name: str = '',
    #              senders: None|set[Node] = None) -> None:
    #     self.tag = Tag.OUTLET
    #     self.name = name if name else self.tag.value
    #     self.__senders = senders if senders else set()
    #     self.operations = transfer_flow

    def __key(self) -> tuple:
        return (self.tag, self.name, type(self.operations))
    def __hash__(self) -> int:
        return hash(self.__key())
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Outlet):
            return False
        return self.__key() == other.__key()
    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def attach_log(self, log: Log) -> Log:
        '''Modifies operations to include logging.'''
        self.operations.operate = log.logger(self.operations.operate)
        log.headers = self.operations.output_labels()
        return log
        # self.operations = log.logger(self.operations)
        # # TODO: add real headers for log from ops.
        # log.headers = ('Outflow',)
        # return log

    def receive(self) -> float:
        # needs to only be inflows in .send() call.
        rcvd = sum(sender.send() for sender in self.senders())
        return rcvd
        #return sum(sender.send() for sender in self.senders())

    def send(self) -> float:
        inflow = self.receive()
        return self.operations.operate(inflow)[1]
        #return self.operations(self)
    def senders(self) -> set[Node]:
        return self.__senders
    def add_sender(self, sender: Node) -> None:
        self.__senders.add(sender)
    def remove_sender(self, sender: Node) -> None:
        self.__senders.remove(sender)
