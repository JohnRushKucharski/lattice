'''Tests diagram.py'''
import unittest

from lattice.node import Inflow, Storage, Outlet
from lattice.system import (process_middle_layer, process_outlet_layer,
                            flatten_layer, flatten_diagram, link_layers,
                            System)

# from lattice.system import (process_middle_layer, process_outlet_layer,
#                              flatten_layer, link_layers)

#from examples.diagrams import simple_diagram, complex_diagram

class TestProcessOutletLayer(unittest.TestCase):
    '''Tests validate outlet layer system diagram utility function.'''
    def test_no_nodes_raises_value_error(self):
        '''Test validate outlet layer.'''
        with self.assertRaises(ValueError):
            process_outlet_layer([])
    def test_multiple_nodes_raises_value_error(self):
        '''Test validate outlet layer.'''
        node1 = Outlet()
        node2 = Outlet()
        with self.assertRaises(ValueError):
            process_outlet_layer([node1, node2])
    def test_multiple_lists_raises_value_error(self):
        '''Test validate outlet layer.'''
        node1 = Outlet()
        node2 = Outlet()
        layer = [[node1], [node2]]
        with self.assertRaises(ValueError):
            process_outlet_layer(layer)
    def test_inflow_node_raises_value_error(self):
        '''Test validate outlet layer.'''
        node = Inflow(data=[])
        with self.assertRaises(ValueError):
            process_outlet_layer([node])

class TestProcessMiddleLayer(unittest.TestCase):
    '''Tests process layer system diagram utility function.'''
    def test_single_node_returns_tuple(self):
        '''Test process layer.'''
        node1 = Inflow()
        layer = [node1]
        self.assertEqual(process_middle_layer(layer), [])

class TestFlattenLayer(unittest.TestCase):
    '''Tests flatten layer system diagram utility function.'''
    def test_flat_layer_returns_input(self):
        '''Test flatten layer.'''
        node1 = Inflow()
        node2 = Inflow()
        layer = [node1, node2]
        self.assertEqual(flatten_layer(layer), layer)
    def test_single_nested_layer_returns_inner_list(self):
        '''Test flatten layer.'''
        node1 = Inflow()
        node2 = Inflow()
        layer = [[node1, node2]]
        self.assertEqual(flatten_layer(layer), layer[0])
    def test_multiple_nested_layers_returns_flattened_list(self):
        '''Test flatten layer.'''
        node1 = Storage()
        node2 = Storage()
        node3 = Inflow()
        node4 = Inflow()
        layer = [[node1, node2], [node3, node4]]
        self.assertEqual(flatten_layer(layer), [node1, node2, node3, node4])
    def test_mixed_lists_and_nodes_returns_flattened_list(self):
        '''Test flatten layer.'''
        node1 = Inflow()
        node2 = Inflow()
        node3 = Inflow()
        node4 = Inflow()
        layer = [node1, [node2, node3], node4]
        self.assertEqual(flatten_layer(layer), [node1, node2, node3, node4])

class TestLinkLayers(unittest.TestCase):
    '''Tests connect nodes system diagram utility function.'''
    def test_single_node_to_single_node(self):
        '''Test connect nodes.'''
        node1 = Outlet()
        node2 = Inflow()
        layer1 = [node1]
        layer2 = [node2]
        link_layers(layer1, layer2, [(0, 0)])
        self.assertEqual(node1.senders(), {node2})
    def test_single_node_to_multiple_nodes(self):
        '''Test connect nodes.'''
        node1 = Outlet()
        node2 = Inflow()
        node3 = Inflow()
        layer1 = [node1]
        layer2 = [[node2, node3]]
        link_layers(layer1, layer2, [(0, 0)])
        self.assertEqual(node1.senders(), {node2, node3})

def simple_diagram():
    '''
    Simple diagram expected simulation values at:
    - inflow_node: [1, 1, 0]
    - storage_node: [(0, 0, (0,)), (1, 1, (0,)), (1, 1, (1,)), (0, 1, (0,))]
    - outlet_node: [0, 1, 0]
    '''
    return [
        [Outlet()],
        [Storage()],
        [Inflow(data=[1, 1, 0])]]

class TestSimpleDiagram(unittest.TestCase):
    '''Tests system class using simple diagram.'''
    def test_format_node_names_simple_diagram_no_changes(self):
        '''Test format node names simple diagram.'''
        system = System(simple_diagram())
        names = [node.name for node in flatten_diagram(system.diagram)]
        self.assertEqual(names, ['outlet', 'storage', 'inflow'])

    def test_simulate_simple_diagram_log_outlet_node(self):
        '''Test simulate log simple diagram.'''
        system = System(simple_diagram())
        logs = system.simulation(3, log_nodes=['outlet'])
        output = logs['outlet'].records_by_label('outflow')
        self.assertEqual(output, [0, 1, 0])

    def test_simulate_simple_diagram_log_storage_node(self):
        '''Test simulate log simple diagram.'''
        system = System(simple_diagram())
        logs = system.simulation(3, log_nodes=['storage'])
        self.assertEqual(logs['storage'].records,
                         [(1.0, 1.0, (0.0,)), (1.0, 1.0, (1.0,)), (0.0, 1.0, (0.0,))])

    def test_simulate_simple_diagram_log_inflow_node(self):
        '''Test simulate log simple diagram.'''
        system = System(simple_diagram())
        logs = system.simulation(3, log_nodes=['inflow'])
        output = logs['inflow'].records_by_label('inflow')
        self.assertEqual(output, [1, 1, 0])

def complex_diagram():
    '''
    Complex digram expected simulation values at:
    layer 0:    outlet_node: 
                [0, 2, 2]
                    |
                    |-----------------.
    layer 1:    storage_node1:      storage_node2:
                [(0, 0, (0,)),      [(0, 0, (0,)),  
                (1, 1, (0,)),       (0, 0, (0,)),
                (1, 1, (1,)),       (2, 1, (1,)),
                (0, 1, (0,))]       (2, 1, (2,))]
                    |                   |
                    |                   |-----------------.
    layer 2:    inflow_node1:       storage_node3:    storage_node4:
                [1, 1, 0]           [(0, 0, (0,)),    [(0, 0, (0,)),    
                                    (1, 1, (0,)),     (1, 1, (0,)),
                                    (1, 1, (1,)),     (1, 1, (1,)),
                                    (1, 1, (1,))]     (1, 1, (1,))]
                                        |                 |
    layer 3:                        inflow_node2:     inflow_node3:   
                                    [1, 1, 1]         [1, 1, 1]`
    '''
    return [
        [Outlet()],
        [ # layer 1
            [ # all nodes in layer 1 are grouped (all send to outlet)
            Storage(),
            Storage()
            ]
        ],
        [ # layer 2
            Inflow(data=[1, 1, 0]),
            [ # group of nodes in layer 2
                Storage(),
                Storage()
            ]
        ],
        [Inflow(data=[1, 1, 1]), Inflow(data=[1, 1, 1])]
    ]

class TestComplexDiagram(unittest.TestCase):
    '''Tests system class using complex diagram.'''
    def test_format_node_names_complex_diagram_appends_ints(self):
        '''Test format node names complex diagram.'''
        system = System(complex_diagram())
        names = [node.name for node in flatten_diagram(system.diagram)]
        self.assertEqual(names,
                         ['outlet',
                          'storage_1', 'storage_2',
                          'inflow_1', 'storage_3', 'storage_4',
                          'inflow_2', 'inflow_3'])

    def test_simulate_complex_diagram_all_nodes(self):
        '''Test simulate log complex diagram.'''
        system = System(complex_diagram())
        logs = system.simulation(3)
        #pylint: disable=unused-variable
        # branch 1
        i1 = logs['inflow_1'].records_by_label('inflow')
        s1 = logs['storage_1'].records

        # branch 2-upleft
        i2n = system.node_by_name('inflow_2')
        s3n = system.node_by_name('storage_2')
        i2 = logs['inflow_2'].records_by_label('inflow')
        s3 = logs['storage_3'].records

        # branch 2-upright
        i3n = system.node_by_name('inflow_3')
        s4n = system.node_by_name('storage_4')
        i3 = logs['inflow_3'].records_by_label('inflow')
        s4 = logs['storage_4'].records
        # branch 2-bottom
        s2n = system.node_by_name('storage_2')
        s2 = logs['storage_2'].records
        # outlet
        o = logs['outlet'].records_by_label('outflow')

        self.assertEqual(o,
                         [0, 2, 2])
        self.assertEqual(logs['storage_1'].records,
                         [(1, 1, (0,)), (1, 1, (1,)), (0, 1, (0,))])
        self.assertEqual(logs['storage_2'].records,
                         [(0, 0, (0,)), (2, 1, (1,)), (2, 1, (2,))])
        self.assertEqual(i1,
                         [1, 1, 0])
        self.assertEqual(logs['storage_3'].records,
                         [(1, 1, (0,)), (1, 1, (1,)), (1, 1, (1,))])
        self.assertEqual(logs['storage_4'].records,
                         [(1, 1, (0,)), (1, 1, (1,)), (1, 1, (1,))])
        self.assertEqual(i2,
                         [1, 1, 1])
        self.assertEqual(i3,
                         [1, 1, 1])
