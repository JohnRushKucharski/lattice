'''
Utility functions for creating and processing system diagram.

Systems in this project can be represented as a list of lists.
- The outer list represents the system.
- Each inner list represents a system layer.

A Layer is a collection of nodes that have the same number
of downstream nodes between them and the system outlet.
- The first layer is the system outlet.
- The last layer contains only inflow nodes.
- Intermediate layers recieve flows from upstream layers
and send flows to downstream layers.

Simple example:
simple_diagram =
[
[outlet_node],  # layer 0 
[storage_node], # layer 1
[inflow_node]   # layer 2
]

A layer may contain a list of Nodes (like the example above),
or a list of Nodes, or a combination of the two.
- The nodes in a a list of nodes within a layer all send flows to the same downstream node.

More complex example:
complex_diagram =
[
[outlet_node],                                  # layer 0
[[storage_node1, storage_node2]]                # layer 1
[inflow_node1, [storage_node3, storage_node4]]  # layer 2                       # layer 2
[inflow_node2, inflow_node3]                    # layer 3
]   

In the example above: 
- Layer 0: contains the system outlet.
- Layer 1: Two storage nodes send flows to the outlet.
- Layer 2: 
    - inflow_node1: sends flow to storage_node1, and
    - storage_node3 and storage_node4: send flow downstream to storage_node2.
- Layer 3:
    - inflow_node2: sends flow to storage_node3, and
    - inflow_node3: send flow to storage_node4.

Graphically: this system looks like this:
 Outlet
    |
    |-------------------.
    |                   |    
    StorageNode1    StorageNode2
    |                   |-------------.
    InflowNode1         |             |
                    StorageNode3    StorageNode4
                        |               |
                     InflowNode2     InflowNode3
'''
import copy

from lattice.node import Node, Log, Tag

# type Links = list[tuple[int, int]]
# type DraftLayer = list[Node|list[Node]]
# type DraftDiagram = list[DraftLayer]
# type Layer = tuple[Node|tuple[Node,...],...]
# type Diagram = tuple[Layer,...]

def link_diagram(diagram: list[list[Node|list[Node]]]) -> list[list[Node|list[Node]]]:
    '''
    Checks diagram structure and links sender-reciever nodes.
    '''
    for i in range(len(diagram)-1):
        cxns = process_outlet_layer(diagram[i]) if i == 0 else process_middle_layer(diagram[i])
        link_layers(diagram[i], diagram[i+ 1], cxns)
    validate_inflow_layer(diagram[-1])
    return diagram

def process_outlet_layer(layer: list[Node|list[Node]]) -> list[tuple[int, int]]:
    '''Validates first (outlet) layer of system diagram and returns its coonections.
    
    Returns:
        Links: always [(0, 0)] for outlet layer.
    Raises:
        ValueError: if outlet layer contains more than one node or non-outlet node.
    '''
    # should contain one node in a single list.
    n = len(layer)
    if n != 1:
        raise ValueError(
            f'''
            The outlet layer must contain a single list with one outlet node.
            {n} nodes or lists found.
            '''
        )
    if layer[0].tag != Tag.OUTLET:
        raise ValueError(
            f'''
            The node in the outlet layer must be an outlet node.
            A {layer[0].tag.value} node found.
            '''
        )
    # return ds, us position of nodes with cxns
    return [(0, 0)]

def process_middle_layer(layer: list[Node|list[Node]]) -> list[tuple[int, int]]:
    '''
    Validates intermediate or layer and 
    returns its connections to upstream nodes and groupd of nodes.

    Returns:
        Links: list of tuples containing downstream and upstream node positions.
    Raises:
        ValueError: if layer contains any outlet nodes.
    '''
    cxns = []
    n, i = 0, 0 # number of nodes, number of inflow nodes

    def process_node(node: Node) -> None:
        nonlocal n, i
        if node.tag == Tag.OUTLET:
            raise ValueError(
                f'''
                The outlet node must be in the first layer of the system diagram.
                An outlet node found in layer {n}.
                '''
            )
        if node.tag == Tag.INFLOW:
            i += 1
        else:
            cxns.append((n, n-i))
        n += 1

    # call process node for each node in layer
    for element in layer:
        if isinstance(element, list):
            for node in element:
                process_node(node)
        else:
            process_node(element)
    return cxns

def flatten_layer(layer: list[Node|list[Node]]) -> list[Node]:
    '''
    Flattens layer of nodes and lists of nodes.
    '''
    nodes = []
    for element in layer:
        if isinstance(element, (list, tuple)):
            if not all(isinstance(subelement, Node) for subelement in element):
                raise ValueError('Invalid element in group. Only nodes are allowed.')
            nodes.extend(element)
        elif isinstance(element, Node):
            nodes.append(element)
        else:
            raise ValueError(f'''Invalid layer. Only nodes or groups of nodes allowed.
                             {type(element)} found.''')
    return nodes

def link_layers(ds: list[Node|list[Node]],
                us: list[Node|list[Node]],
                cxns: list[tuple[int, int]]) -> None:
    '''
    Links downstream and upstream nodes in adjacent layers.

    Returns:
        None: modifies nodes in place.
    Raises:
        ValueError: if downstream or upstream node positions are out of range.
    '''
    ds_flat = flatten_layer(ds)
    for cxn in cxns:
        if cxn[0] >= len(ds_flat):
            raise ValueError(f'''
                Downstream node position {cxn[0]} is out of range.
                Only {len(ds_flat)} nodes found.''')
        if cxn[1] >= len(us):
            raise ValueError(f'''
                Upstream node position {cxn[1]} is out of range.
                Only {len(us)} nodes or node groups found.''')
        # link ds node to us element.
        # us could be node or list of nodes.
        us_part = us[cxn[1]]
        ds_node = ds_flat[cxn[0]]
        if isinstance(us_part, list):
            for node in us_part:
                ds_node.add_sender(node)
        else:
            ds_node.add_sender(us_part)

def validate_inflow_layer(layer: list[Node|list[Node]]) -> None:
    '''
    Validates inflow (last) layer of system diagram.

    Raises:
        ValueError: if inflow layer contains any non-inflow nodes.
    '''
    layer = flatten_layer(layer)
    for node in layer:
        if node.tag != Tag.INFLOW:
            raise ValueError(
                f'''
                The inflow layer must contain only inflow nodes.
                A {node.tag.value} node found.
                '''
            )

def flatten_diagram(diagram: list[list[Node|list[Node]]]) -> tuple[Node,...]:
    '''Creates a flat list of nodes from a system diagram.'''
    nodes = []
    for layer in diagram:
        if not isinstance(layer, (list, tuple)):
            raise ValueError('''Invalid diagram. Diagram must be composed of list of layers.''')
        nodes.extend(flatten_layer(layer))
    return tuple(nodes)

def fix_diagram(diagram: list[list[Node|list[Node]]]) -> tuple[tuple[Node|tuple[Node,...],...],...]:
    '''Fixes system diagram structure by converting lists to tuples.'''
    _diagram = []
    for layer in diagram:
        _layer = []
        for element in layer:
            if isinstance(element, list):
                _layer.append(tuple(element))
            else:
                _layer.append(element)
        _diagram.append(tuple(_layer))
    return tuple(_diagram)

class System:
    '''
    A system is a collection of nodes that are connected in a specific way.
    '''
    def __init__(self, diagram: list[list[Node|list[Node]]]) -> None:
        self.diagram = fix_diagram(link_diagram(diagram))
        self.format_node_names() # sets unique names for nodes, modifies diagram in place.


        #self.logs = {node: node.log for node in flatten_diagram(diagram) if not node.log is None}

    def node_by_name(self, name: str) -> Node:
        '''
        Return node by name.
        '''
        for node in flatten_diagram(self.diagram):
            if node.name == name:
                return node
        raise ValueError(f'Node {name} not found in system.')

    def format_node_names(self) -> None:
        '''
        Format node names so no duplicates exist.
        '''
        names = []
        dupes = []
        for node in flatten_diagram(self.diagram):
            i: int = 2 # original set to name + 1 later
            name = node.name
            while name in names:
                if i == 2: # first pass
                    dupes.append(name)
                name = f'{node.name}_{i}'
                i += 1
            node.name = name
            names.append(name)
        # set original to name + 1
        for name in dupes:
            for node in flatten_diagram(self.diagram):
                if node.name == name:
                    node.name = f'{name}_1'

    def add_logs(self, names: None|tuple[str,...]) -> dict[str, Log]:
        '''
        Adds logs to nodes in the system.
        
        Args:
            names(tuple[str,...]): tuple of node names to add logs to.

        Returns:
            dict[str, Log]: node names (keys) and node logs (values).
        '''
        logs = {}
        if names is None:
            names = [node.name for node in flatten_diagram(self.diagram)]
        for name in names:
            node = self.node_by_name(name)
            log = node.attach_log(Log())
            logs[name] = log
        return logs

    def simulation(self, time_steps: int, log_nodes: None|tuple[str,...]=None) -> dict[str, Log]:
        '''
        Run the system and return the outflows from the outlet node.

        Args:
            time_steps(int): number of time steps to run the simulation.
            log_nodes(None|tuple[str,...]): tuple of node names to log.
                None by default, if None, all nodes are logged.

        Returns:
            dict[str, Log]: node names (keys) and node logs (values).
        '''
        # set up.
        system = copy.deepcopy(self)
        logs = system.add_logs(log_nodes)

        # run simulation.
        outlet = system.diagram[0][0]
        for _ in range(time_steps):
            outlet.send()
        return logs
