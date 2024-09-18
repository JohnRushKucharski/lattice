'''Tests diagram.py'''

import unittest

from lattice.node import Inflow, Storage, Outlet
from lattice.system import (process_middle_layer, process_outlet_layer,
                            flatten_layer, flatten_diagram, link_layers,
                            System)

# from lattice.system import (process_middle_layer, process_outlet_layer,
#                              flatten_layer, link_layers)

from examples.diagrams import simple_diagram, complex_diagram

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
        node = Inflow([])
        with self.assertRaises(ValueError):
            process_outlet_layer([node])

class TestProcessMiddleLayer(unittest.TestCase):
    '''Tests process layer system diagram utility function.'''
    def test_single_node_returns_tuple(self):
        '''Test process layer.'''
        node1 = Inflow([])
        layer = [node1]
        self.assertEqual(process_middle_layer(layer), [])

class TestFlattenLayer(unittest.TestCase):
    '''Tests flatten layer system diagram utility function.'''
    def test_flat_layer_returns_input(self):
        '''Test flatten layer.'''
        node1 = Inflow([])
        node2 = Inflow([])
        layer = [node1, node2]
        self.assertEqual(flatten_layer(layer), layer)
    def test_single_nested_layer_returns_inner_list(self):
        '''Test flatten layer.'''
        node1 = Inflow([])
        node2 = Inflow([])
        layer = [[node1, node2]]
        self.assertEqual(flatten_layer(layer), layer[0])
    def test_multiple_nested_layers_returns_flattened_list(self):
        '''Test flatten layer.'''
        node1 = Storage()
        node2 = Storage()
        node3 = Inflow([])
        node4 = Inflow([])
        layer = [[node1, node2], [node3, node4]]
        self.assertEqual(flatten_layer(layer), [node1, node2, node3, node4])
    def test_mixed_lists_and_nodes_returns_flattened_list(self):
        '''Test flatten layer.'''
        node1 = Inflow([])
        node2 = Inflow([])
        node3 = Inflow([])
        node4 = Inflow([])
        layer = [node1, [node2, node3], node4]
        self.assertEqual(flatten_layer(layer), [node1, node2, node3, node4])

class TestLinkLayers(unittest.TestCase):
    '''Tests connect nodes system diagram utility function.'''
    def test_single_node_to_single_node(self):
        '''Test connect nodes.'''
        node1 = Outlet()
        node2 = Inflow([])
        layer1 = [node1]
        layer2 = [node2]
        link_layers(layer1, layer2, [(0, 0)])
        self.assertEqual(node1.senders(), {node2})
    def test_single_node_to_multiple_nodes(self):
        '''Test connect nodes.'''
        node1 = Outlet()
        node2 = Inflow([])
        node3 = Inflow([])
        layer1 = [node1]
        layer2 = [[node2, node3]]
        link_layers(layer1, layer2, [(0, 0)])
        self.assertEqual(node1.senders(), {node2, node3})

class TestSystem(unittest.TestCase):
    '''Tests system class.'''
    def test_format_node_names_simple_diagram_no_changes(self):
        '''Test format node names simple diagram.'''
        system = System(simple_diagram)
        names = [node.name for node in flatten_diagram(system.diagram)]
        self.assertEqual(names, ['outlet', 'storage', 'inflow'])

    def test_format_node_names_complex_diagram_appends_ints(self):
        '''Test format node names complex diagram.'''
        system = System(complex_diagram)
        names = [node.name for node in flatten_diagram(system.diagram)]
        self.assertEqual(names,
                         ['outlet',
                          'storage_1', 'storage_2',
                          'inflow_1', 'storage_3', 'storage_4',
                          'inflow_2', 'inflow_3'])

    def test_simulate_simple_diagram_log_outlet_node(self):
        '''Test simulate log simple diagram.'''
        system = System(simple_diagram)
        logs = system.simulation(3, log_nodes=['outlet'])
        self.assertEqual(logs['outlet'].records, [0, 1, 0])

    def test_simulate_simple_diagram_log_storage_node(self):
        '''Test simulate log simple diagram.'''
        system = System(simple_diagram)
        logs = system.simulation(3, log_nodes=['storage'])
        self.assertEqual(logs['storage'].records,
                         [(0, 0, (0,)), (1, 1, (0,)), (1, 1, (1,)), (0, 1, (0,))])

    def test_simulate_simple_diagram_log_inflow_node(self):
        '''Test simulate log simple diagram.'''
        system = System(simple_diagram)
        logs = system.simulation(3, log_nodes=['inflow'])
        self.assertEqual(logs['inflow'].records, [1, 1, 0])

    def test_simulate_complex_diagram_all_nodes(self):
        '''Test simulate log complex diagram.'''
        system = System(complex_diagram)

        logs = system.simulation(3)
        i2 = logs['inflow_2'].records
        s3 = logs['storage_3'].records

        i3 = logs['inflow_3'].records
        s4 = logs['storage_4'].records

        s2 = logs['storage_2'].records

        i1 = logs['inflow_1'].records
        s1 = logs['storage_1'].records

        o = logs['outlet'].records

        self.assertEqual(logs['outlet'].records, [0, 2, 2])
        self.assertEqual(logs['storage_1'].records,
                         [(0, 0, (0,)), (1, 1, (0,)), (1, 1, (1,)), (0, 1, (0,))])
        self.assertEqual(logs['storage_2'].records,
                         [(0, 0, (0,)), (0, 0, (0,)), (2, 1, (1,)), (2, 1, (2,))])
        self.assertEqual(logs['inflow_1'].records, [1, 1, 0])
        self.assertEqual(logs['storage_3'].records,
                         [(0, 0, (0,)), (1, 1, (0,)), (1, 1, (1,)), (1, 1, (1,))])
        self.assertEqual(logs['storage_4'].records,
                         [(0, 0, (0,)), (1, 1, (0,)), (1, 1, (1,)), (1, 1, (1,))])
        self.assertEqual(logs['inflow_2'].records, [1, 1, 1])
        self.assertEqual(logs['inflow_3'].records, [1, 1, 1])
