'''
A tree represenation of the system.
'''
from dataclasses import dataclass

from lattice.node import Tag, Node

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

def find_all(row: str, chars: str|tuple[str,...]) -> list[int]:
    '''
    Find all positions of a character in a string.
    '''
    return [i for i, c in enumerate(row) if c in chars]

#region: Image Utilities
def update_counts(node: Node, counts: dict[Tag, int]) -> tuple[int, dict[Tag, int]]:
    '''
    Returns the type count label for a node.
    '''
    match node.tag:
        case Tag.OUTLET:
            if counts[Tag.OUTLET] == 0:
                counts[Tag.OUTLET] += 1
                return counts[Tag.OUTLET], counts
            else:
                raise ValueError('Only one outlet node per diagram allowed.')
        case Tag.INFLOW:
            counts[Tag.INFLOW] += 1
            return counts[Tag.INFLOW], counts
        case Tag.STORAGE:
            counts[Tag.STORAGE] += 1
            return counts[Tag.STORAGE], counts
        case _:
            raise NotImplementedError(f'Node tag {node.tag} not implemented.')

def label_node(node: Node, n: int) -> str:
    '''
    Provides string representation of node for image, in format:
        [Xn] where X is the node tag and n is the node type count.
    '''
    match node.tag:
        case Tag.OUTLET:
            return '[O]'
        case Tag.INFLOW:
            return f'[I{n}]'
        case Tag.STORAGE:
            return f'[S{n}]'
        case _:
            raise NotImplementedError(f'Node tag {node.tag} not implemented.')

def add_node(node_row: str, node_label: str, node_pos: int) -> str:
    '''
    Adds a node to a row.
    '''
    if (n:= node_pos - len(node_row)) < 0:
        if n == -1:
            node_row = node_row[:node_pos] + node_label
        else:
            node_row = node_row[:node_pos] + node_label + node_row[node_pos+len(node_label):]
        return node_row
    return node_row + ' ' * (node_pos - len(node_row)) + node_label

def find_node_positions(node_row: str, chars: str|tuple[str,...] = '|') -> list[int]:
    '''
    Finds positions of nodes in a row.
    '''
    offset = -1
    positions = find_all(node_row, chars)
    return [pos + offset for pos in positions]

def find_trunk_positions(node_row: str, chars: str|tuple[str,...]) -> list[int]:
    '''
    Finds positions of trunks in a row.
    '''
    positions = []
    for _, c in enumerate(chars):
        match c:
            case '|' | "'":
                positions.extend(find_all(node_row, c))
            case '[':
                offset = 1
                locs = find_all(node_row, c)
                locs = [loc + offset for loc in locs]
                positions.extend(locs)
            case _:
                raise ValueError(f'Invalid character {c} in chars.')
    return positions

def add_trunk(trunk_row: str, trunk_pos: int, overwrite: bool = False) -> str:
    '''
    Adds trunk at a specified position.
    
    Example:
                      location 
                      v
                    0123456789
        trunk_row     |        <- this is what is added.
                    0123456789
                      ^
                      start_node
                      v    
                    0123456789
        node_row     [Xi]        
                    0123456789                 
    '''
    if (n:= trunk_pos - len(trunk_row)) < 0:
        if overwrite:
            trunk_row = trunk_row[:trunk_pos] + '|' + trunk_row[trunk_pos+1:]
        else: # insert (not overwrite)
            trunk_row = trunk_row[:trunk_pos] + '|' + trunk_row[trunk_pos:]
        return trunk_row
    return trunk_row + ' ' * n + '|' #maybe n-1

def add_trunks(trunk_row: str, search_row: str,
               chars: str|tuple[str,...] = '[', overwrite: bool = False) -> str:
    '''
    Adds trunks above all nodes in a row.
    '''
    positions = find_trunk_positions(search_row, chars)
    for pos in positions:
        trunk_row = add_trunk(trunk_row, pos, overwrite)
    return trunk_row

#endregion: Image Utilities

@dataclass
class Diagram:
    '''
    A tree representation of the system.
    '''
    tree: list[list[Node|list[Node]]]

    def layer(self, i: int) -> list[Node|list[Node]]:
        '''
        Returns a layer of the diagram.
        '''
        if 0 <= i < len(self.tree):
            return self.tree[i]
        raise ValueError(f"Index {i} out of range for tree with {len(self.tree)} layers.")

    def flatten_layer(self, i: int) -> list[Node]:
        '''
        Returns a layer of the diagram.
        '''
        return flatten_layer(self.layer(i))

    #region: Image
    def create_image(self):
        '''
        Create an image of the diagram.
        '''
        counts = {
            Tag.OUTLET: 0,
            Tag.INFLOW: 0,
            Tag.STORAGE: 0
        }
        image = []
        for i, layer in enumerate(self.tree):
            node_row, trunk_row = '', ''
            for j, node in enumerate(flatten_layer(layer)):
                n, counts = update_counts(node, counts)
                if i == 0:
                    image = self.add_outlet(node, n,
                                            node_row, 1, trunk_row)
                else:
                    rows = self.add_middle_layer_node(node, n,
                                                      node_row, image[-1])

    def add_branches(self, trunk_row: str, i: int, j: int, node: None|Node = None) -> str:
        '''
        Appends branches on trunk row.
        
        Parameters:
        ----------
        trunk_row: str
            Example:
                '  |    |'   <- trunk row.
                ' [Xi] [Xi]' <- node row.
        node: Node
            Node to add branches for.
        i: int 
            Index of layer containing node.
        j: int
            Index of node in layer.
        node: None|Node
            Optional: node for which branches are added.
            Used to check diagram structure. None by default.
            
        Returns: str
            Trunk row with branches added.
            
            Example:
                Adding 2 branches to node [S2]
                '  |    |----'----'   <- trunk row is copied, branches added.
                '  |    |'            <- trunk row.
                ' [S1] [S2]'          <- node row.            
        '''
        if i + 1 < len(self.tree):
            layer_above = self.layer(i + 1)
            element = layer_above[j]
            if isinstance(element, Node):
                return trunk_row # no branches to add.
            else: # element is a list of nodes.
                branches = len(element) # nodes.
                if node:
                    if node.tag == Tag.INFLOW:
                        raise ValueError('Inflow nodes cannot have branches.')
                    # if len(node.senders()) != branches:
                    #     raise ValueError(f'''
                    #                  Invalid connections for node {node}.
                    #                  Expecting {len(node.senders())} connections, found {branches}.
                    #                  ''')
                if branches < 2:
                    # either [] or [node]
                    raise ValueError(f'''
                                     Invalid connections for node {node}.
                                     Expecting group of nodes, found {len(element)}.
                                     ''')
                return trunk_row + ("----'" * (branches - 1))
    def add_outlet(self, node: Node, n: int = 1,
                   node_row = '', node_pos: int = 1,
                   trunk_row = '') -> list[str]:
        '''
        Adds outlet node to diagram.
        '''
        rows = []
        rows.append('')                                                             # '' empty row.
        rows.append(add_node(node_row, label_node(node, n), node_pos))              # ' [O]'
        rows.append(add_trunk(trunk_row, find_trunk_positions(rows[-1], '[')[-1]))  # '  |'
        rows.append(self.add_branches(rows[-1], 0, 0, node))                        # '  |----'...'
        rows.append(add_trunks('', rows[-1], ("|", "'")))                      # '  |    |'
        return rows

    def add_middle_layer_node(self, node: Node, n: int, i: int, j: int,
                              node_row: str = '', trunk_row: str = '') -> list[str]:
        '''
        Adds middle layer to diagram.
        '''
        rows = []
        rows.append(add_node(node_row, label_node(node, n),
                             find_node_positions(trunk_row, ("|", "'"))[j]))
        rows.append(add_trunk('', find_trunk_positions(rows[-1], '[')[j]))
        rows.append(self.add_branches(rows[-1], i, j, node))
        rows.append(add_trunks(rows[-1], rows[0], ("|", "'")))
        return rows
    #endregion: Image
