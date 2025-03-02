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
import re
from lattice.node import Node, Log, Tag

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

# def create_image(diagram: list[list[Node|list[Node]]]) -> list[str]:
#     '''
#     Creates an image of the system diagram.
#     '''
#     counts = {
#         Tag.OUTLET: 0,
#         Tag.INFLOW: 0,
#         Tag.STORAGE: 0
#     }

#     def label_node(node: Node) -> str:
#         '''
#         Provides string representation of node for image, in format:
#             [Xn] where X is the node tag and n is the node number.
#         '''
#         if node.tag == Tag.OUTLET:
#             counts[Tag.OUTLET] += 1
#             return '[O]'
#         else:
#             def node_number(name: str) -> int:
#                 if num := name.split('_')[-1].isdigit():
#                     return num
#                 return counts[node.tag]
#             match node.tag:
#                 case Tag.INFLOW:
#                     counts[Tag.INFLOW] += 1
#                     return f'[I{node_number(node.name)}]'
#                 case Tag.STORAGE:
#                     counts[Tag.STORAGE] += 1
#                     return f'[S{node_number(node.name)}]'
#                 case _:
#                     raise NotImplementedError(f'Node tag {node.tag} not implemented.')

#     def add_trunk_above_node(row: str, end_node: int) -> str:
#         '''
#         Adds trunk above a node.
#                    location 
#                    v 
#                  0123456789
#                 1  |        <- this is what is added.
#                 0 [xi] 
#                  0123456789
#                      ^
#                      end_node
#         '''
#         spaces = f'{" " * end_node - len(row)}'
#         spaces[-3] = '|'
#         return row + spaces

#     def add_branches(n: int) -> str:
#         '''
#         Adds branches above a node.
#                      0123456789
#             next    - [xi] [xi]    
#             row3    3  |    |
#             row2    2  |----'    
#             row1    1  |    
#             row0    0 [xi]
#                      0123456789
#         '''
#         return "----'" * n

#     def render_outlet(layer: list[Node|list[Node]]) -> list[str]:
#         '''
#         Renders the outlet layer of the system diagram.
#         '''
#         rows = [f' {label_node(layer[0])}']
#         rows.append(add_trunk_above_node([], len(rows[0])))
#         rows.append(add_trunk_above_node([], len(rows[0])))
#         # add branches.
#         #rows.append(add_trunk_above_node([]))
#         return rows

#     def find_all(row: str, char: str = '|') -> list[int]:
#         '''
#         Find all positions of a character in a string.
#         '''
#         return [i for i, c in enumerate(row) if c == char]

#     def validate_node_positions(flat_layer: list[Node], node_positions: list[int]) -> None:
#         '''
#         Checks if node positions are valid.
#         '''
#         if len(flat_layer) != len(node_positions):
#             raise ValueError(f'''
#                              Number of nodes {len(flatten_layer)} does not match 
#                              number of node positions {len(node_positions)}.''')

#     def add_node(row: list[str], node: Node, pos: int) -> str:
#         '''
#         Renders node on trunk.
#                      len(row)= 4
#                      |  pos  = 7
#                      v  v     
#                  0123456789
#           row > 2 [xi]
#                 1  |    |
#                 0 [xi] [xi]
#                  0123456789
#                       ^^
#                       |offset = 2 (white space to pos)
#                       whitespace = pos - len(row) - offset
        
#         Returns: new right side of row " [xi]" (to existing " [xi]").              
#         '''
#         offset = 2
#         if pos < len(row):
#             raise ValueError(f'''Position {pos} for next node
#                              is out of range for row with length {len(row)}.''')
#         whitespace: int = pos - len(row) - offset
#         return f'{" " * whitespace}{label_node(node)}'
    
#     def is_middle_layer(diagram: list[list[Node|list[Node]]], i: int) -> bool:
#         '''
#         Checks if layer is inflow layer.
#         '''
#         return i < len(diagram) - 1

#     def count_branches(layer: list[Node|list[Node]], j: int) -> int:
#         '''
#         Counts branches in layer above.
#         '''
#         element = layer[j]
#         if isinstance(element, (list, tuple)):
#             return len(element)
#         return 1 # single node.
        
#     def render_layer(diagram: list[list[Node|list[Node]]], i: int,
#                      image: None|list[str]) -> list[str]:
#         if i == 0:
#             # outlet layer.
#             return render_outlet(diagram[i])
#         # inflow or middle layer.
#         layer = flatten_layer(diagram[i])
#         node_positions = find_all(image[-1], "|")
#         validate_node_positions(layer, node_positions)
#         row0 = [] # row with nodes.
#         row1 = [] # row with trunks.
#         row2 = [] # row with branches.
#         row3 = [] # row with trunks above branches.
#         for j, node in enumerate(layer):
#             row0.append(add_node(row0, node, node_positions[j]))
#             if is_middle_layer(diagram, i):
#                 row1.append(add_trunk_above_node(row1, len(row0)))
#                 branches = count_branches(diagram[i+1], j)
#                 row2 = row1.copy()
                
#         image.append(row0)
#         if is_middle_layer(diagram, i):
#             image.append(row0) #  |
#             image.append(row1) #  |
#             image.append(row2) #  |
#         return image

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
    '''
    Validates first (outlet) layer of system diagram.
    
    Parameters:
        layer: list of nodes in the outlet layer.
        If more than a single node is present, the function raises a ValueError.
    
    Returns:
        Links: list (cxns) always [(0, 0)] for outlet layer, 
        
        Notes:
        [1] Each tuple is: (ds: int, us: int) where,
            ds: downstream node position in layer (list of nodes).
            us: upstream node position in layer (list of nodes).
        [2] ds is the single outlet node, therefore must be at position 0.
        [3] us all upstream nodes must flow into the outlet node and 
            therefore also be at position 0 in the us layer. If more than one
            us node is present, the must be grouped in a list.   
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
    returns its connections to upstream nodes and groups of nodes.

    Returns:
        Links: list (cxns) of tuples containing downstream and upstream node positions.
        
        Notes: 
        [1] Each tuple is: (ds: int, us: int) where,
            ds: downstream node position in layer (list of nodes).
            us: upstream node position in layer (list of nodes),
                same as current position (n) minus inflow nodes (i)
                since inflow nodes have no upstream cxns.
        [2] ds is n (position of current node in layer)
    Raises:
        ValueError: if layer contains any outlet nodes.
    '''
    cxns = []
    n, i = 0, 0 # n: number of nodes, i: number of inflow nodes

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
            # no connections for inflow nodes.
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
        # TODO: do I really need a deep copy here?
        #system = copy.deepcopy(self)
        logs = self.add_logs(log_nodes)

        # run simulation.
        outlet = self.diagram[0][0]
        for _ in range(time_steps):
            outlet.send()
        return logs

# @dataclass
# class Diagram:
#     '''
#     A system diagram.
#     '''
#     diagram: list[list[Node|list[Node]]]
    
#     def __post_init__(self):
#         is_valid: bool = True
#         layers: int = len(self.diagram)
        
    

# def print_diagram(diagram: list[list[Node|list[Node]]]) -> list[list[str]]:
#     '''
#     Prints a tree representation of the system diagram.
#     '''
#     counts = {
#         Tag.OUTLET: 0,
#         Tag.INFLOW: 0,
#         Tag.STORAGE: 0
#     }
#     grid: list[str] = [] #image.
#     # each str is a row in image.
#     for i, layer in enumerate(diagram):
#         pass

# def print_layer(grid: list[str], idx: int,
#                 diagram: list[list[Node|list[Node]]],
#                 counts: dict[Tag, int]) -> list[str]:
#     '''
#     Prints rows of image associated with a layer, with following pattern:
#      0123456789      0123456789
#     3  |     |      3  |
#     2  |-----'      2  |
#     1  |        or  1  |        or  1
#     0 [xi] ...      0 [xi] ...      0 [Ii]  [xi]  
#      0123456789^     0123456789^     0123456789^
#                10              10              10
#     '''
#     node_count = 0
#     inflow_count = 0
#     layer = diagram[idx]
#     node_count, inflow_count = 0, 0
#     rows = [[] for _ in range(4)]
#     # except outlet layer, new nodes placed ontop of "|".
#     node_positions = [0] if idx == 0 else [m.start() for m in re.finditer('|', grid[-1])]
#     i: int = 0 # node position in layer.
#     for element in layer:
#         nodes = element if isinstance(element, (list, tuple)) else [element]
#         for node in nodes:
#             # place [xi] node labels on row 0.
#             label = print_node(node, counts)
#             if idx == 0:
#                 # outlet layer
#                 rows[0] += f' {label}'
#             else:
#                 # put ontop "|"
#                 pipe = node_positions[i]
#                 white_space = ' ' * (pipe - 2)
#                 rows[0] += f'{white_space}{label}'
#             # add pipes and branches.
#             if node.tag != Tag.INFLOW:
#                 pipe = node_positions[i]
#                 index = node_count - inflow_count
                
                
#                 branches = count_branches(diagram[idx+1], index)
#                 rows[1].append("  |")
#                 rows[2].append("  |")
                
#                 rows[3].append("  |")
#             else:
#                 inflow_count += 1
#             count += 1
        
# def print_node(node: Node, counts: dict[Tag, int]) -> str:
#     '''
#     String representation of node for image.
#     '''
#     labels = {
#         Tag.OUTLET: 'O',
#         Tag.INFLOW: 'I',
#         Tag.STORAGE: 'S'
#     }
#     if num:= node.name.split('_')[-1].isdigit():
#         label = f'{node.tag.value}{num}'
#     else:
#         label = f'{node.tag.value}{counts[node.tag]}'
#     counts[node.tag] += 1
#     return f'[{label}]'

# def count_branches(uplayer: list[Node|list[Node]], idx: int) -> int:
#     '''
#     Count branches in layer above.
#     '''
#     branches = uplayer[idx]
#     if isinstance(branches, (list, tuple)):
#         return len(branches)
#     return 1 # single node.
    
#     def print_diagram(self) -> None:
#         '''
#         Prints a tree representation of the system diagram.
#         '''
#         labels = {
#             Tag.OUTLET: 'O',
#             Tag.INFLOW: 'I',
#             Tag.STORAGE: 'S'
#         }
#         counts = {
#             Tag.OUTLET: 0,
#             Tag.INFLOW: 0,
#             Tag.STORAGE: 0
#         }
#         grid: list[list[str]] = [[]] # image of diagram.
#         position: tuple[int, int] = (1, 1) # x, y in grid
#         def label_node(node: Node, grid: list[list[str]], layer_row: int,
#                        ) -> list[list[str]]:
#             nonlocal counts
#             nonlocal labels
#             nonlocal position
#             if num:= node.name.split('_')[-1].isdigit():
#                 label = f'{labels[node.tag]}{num}'
#             else:
#                 label = f'{labels[node.tag]}{counts[node.tag]}'
#             counts[node.tag] += 1
#             for char in label:
#                 grid[layer_row].append(char)
#             return f'[{label}]'
#         def count_branches(base: Node|tuple[Node,...]) -> int:
#             if isinstance(base, (list, tuple)):
#                 return len(base)
#             else:
#                 return 0
#         def count_branches_above(node: Node, layer: int, trunk: int):
#             branches = 0 # n if inflow.
#             if node.tag != Tag.Inflow:
#             # should be at least one more layer above.
#                 element_above = self.diagram[layer+1][trunk]
#                 if isinstance(element_above, (list, tuple)):
#                     branches = len(element_above)
#                 else:
#                     branches = 1
#             return branches

#         base: int = 0 # current level
#         # moves up tree starting at base (outlet).
#         while base < len(self.diagram): # nLayers.
#             # current base layer.
#             layer = self.diagram[base]
#             layer_row = len(grid) # current row.
#             grid.append([' ']) # new row for layer.
#             '''
#             Each layer will look something like this:
#             5 [xi] [xi] 
#             5  |    |
#             4  -----'
#             3  |
#             2  |  
#             1 [xi]
#             0      
#              0123456789
#             '''
#             trunk: int = 0 # one or more branches.
#             while trunk < len(layer):
#                 element = layer[trunk]
#                 # could be node (leaf) or list of nodes (branches).
#                 branches = count_branches(element)
#                 if branches == 0: # leaf on trunk.
                    
#                     grid = label_node(element, grid, layer_row)
                
             
#             ntrunks = len(layer) 
        
        
#         for i, layer in enumerate(self.diagram):
#             # base of current branch
#             base = layer[branch]
#             branches = count_branches(base)
            
            
#             if isinstance(trunk, (list, tuple)): # branches again
#                 branches = len(trunck)
#                 for node in leaf:
#                     label = label_node(node)
#             else:
#                 label = label_node(leaf)
        
        
#         for i, layer in enumerate(self.diagram):
#             cxns = []
#             for j, element in enumerate(layer):
#                 if isinstance(element, (list, tuple)):
#                     for node in element:
#                         label = label_node(node)
#                 else:
#                     label = label_node(element)

                
    
