'''
Tests diagram.py.
'''
import unittest

from lattice.diagram import (Diagram,
                             flatten_layer,
                             find_all, update_counts,
                             label_node, add_node,
                             add_trunk, add_trunks)
from lattice.node import Tag, Outlet, Storage, Inflow
from lattice.system import System

def simple_diagram():
    '''Return a simple diagram.'''
    return Diagram(tree=[
        [Outlet()],
        [Storage()],
        [Inflow(data=[1, 2, 3])]])

def complex_diagram():
    '''Return a complex diagram.'''
    return Diagram(tree=[
        [Outlet()],
        [[Storage(), Storage()]],
        [Inflow(data=[1, 1, 0]), [Storage(), Storage()]],
        [Inflow(data=[1, 1, 1]), Inflow(data=[1, 1, 1])]])

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

class TestFindAll(unittest.TestCase):
    '''Tests find all system diagram utility function.'''
    def test_find_all(self):
        '''Test find all.'''
        self.assertEqual(find_all(' [O]', '['), [1])
        self.assertEqual(find_all(' [I1] [I2]     [I3]', '['), [1, 6, 15])
        self.assertEqual(find_all('  |    |        |', '['), [])
    def test_find_all_tuple_chars(self):
        '''Test find all.'''
        self.assertEqual(find_all(' [O]', ('[',)), [1])
        self.assertEqual(find_all(' [I1] [I2]     [I3]', ('[',)), [1, 6, 15])
        self.assertEqual(find_all('  |    |        |', ('[',)), [])
        # more than one char.
        self.assertEqual(find_all(' [S1]', ('[', ']')), [1, 4])
        self.assertEqual(find_all("  |    |----'", ("|", "'")), [2, 7, 12])

class TestUpdateCounts(unittest.TestCase):
    '''Tests update counts system diagram utility function.'''
    def test_update_counts(self):
        '''Test update counts method.'''
        counts = {Tag.OUTLET: 0, Tag.INFLOW: 0, Tag.STORAGE: 0}
        i, counts = update_counts(Outlet(), counts)
        self.assertEqual(i, 1)
        self.assertEqual(counts, {Tag.OUTLET: 1, Tag.INFLOW: 0, Tag.STORAGE: 0})

        i, counts = update_counts(Storage(), counts)
        self.assertEqual(i, 1)
        self.assertEqual(counts, {Tag.OUTLET: 1, Tag.INFLOW: 0, Tag.STORAGE: 1})

        i, counts = update_counts(Inflow(), counts)
        self.assertEqual(i, 1)
        self.assertEqual(counts, {Tag.OUTLET: 1, Tag.INFLOW: 1, Tag.STORAGE: 1})

        with self.assertRaises(ValueError):
            update_counts(Outlet(), counts)

class TestLabelNode(unittest.TestCase):
    '''
    Tests the label_node system diagram utility function.
    '''
    def test_label_node(self):
        '''Test label node method.'''
        label = label_node(Outlet(), 1)
        self.assertEqual(label, '[O]')

        label = label_node(Storage(), 1)
        self.assertEqual(label, '[S1]')

        label = label_node(Inflow(), 1)
        self.assertEqual(label, '[I1]')

class TestAddTrunk(unittest.TestCase):
    '''
    Tests add trunk system diagram utility methods.
    '''
    def test_add_trunk_to_empty_row(self):
        '''Test add trunk node method.'''
        row = add_trunk('', 2)
        self.assertEqual(row, '  |')
    def test_add_trunk_to_existing_row(self):
        '''Test add trunk to existing row.'''
        row = add_trunk('  |', 7)
        #                      0123456789
        #                     ' [xi] [xi]
        self.assertEqual(row, '  |    |')
    def test_add_trunk_end_of_existing_row(self):
        '''Test add trunk to end of row.'''
        # edit last index
        #                0123456789
        row = add_trunk(' ', 1)
        #                      0123456789
        self.assertEqual(row, ' |')
    def test_insert_trunk_in_middle_of_existing_row(self):
        '''Test insert trunk in middle of row.'''
        #                0123456789
        row = add_trunk('    ', 1)
        #                      0123456789
        self.assertEqual(row, ' |   ')
    def test_insertion_at_correct_position(self):
        '''Test insert trunk at correct position.'''
        #                0123456789
        row = add_trunk('xxzz', 2)
        #                      0123456789
        self.assertEqual(row, 'xx|zz')
    def test_add_trunks_empty_row(self):
        '''Test add trunks method.'''
        row = add_trunks('', ' [O]')
        self.assertEqual(row, '  |')
        # multiple trunks empty row.
        row = add_trunks('',  ' [S1] [S2]')
        self.assertEqual(row, '  |    |')
    def test_add_trunks_existing_row_insert(self):
        ''' test multiple trunks existing row with insert.'''
        #                 0123456789
        #                ' [S1] [S2]'
        row = add_trunks('  |',  ' [S1] [S2]')
        self.assertEqual(row,    '  ||   |')
        # multiple trunks existing row.
        #                 0123456789
        #                ' [S1] [S2]'
        row = add_trunks('  x    x',  ' [S1] [S2]')
        self.assertEqual(row,         '  |x   | x')
    def test_add_trunks_existing_row_overwrite(self):
        ''' test multiple trunks existing row with overwrite.'''
        row = add_trunks('  |',  ' [S1] [S2]', '[', True)
        self.assertEqual(row,    '  |    |')
        # multiple trunks existing row.
        row = add_trunks('  x    x',  ' [S1] [S2]', '[', True)
        self.assertEqual(row,         '  |    |')

class TestAddNode(unittest.TestCase):
    '''
    Tests add node system diagram utility methods.
    '''
    def test_add_node(self):
        '''Test add node method.'''
        row = add_node('', label_node(Outlet(), 1), 1)
        self.assertEqual(row, ' [O]')
        # non-empty row.
        row = add_node(' ', label_node(Storage(), 1), 1)
        self.assertEqual(row, ' [S1]')
        # overwrite existing space.
        row = add_node(' xxxx', label_node(Inflow(), 1), 1)
        self.assertEqual(row, ' [I1]')
        # partially overwrite existing space.
        row = add_node(' xxx', label_node(Inflow(), 1), 1)
        self.assertEqual(row, ' [I1]')

class TestIntegrations(unittest.TestCase):
    '''Groups image utilty functions used to build images.'''
    def test_build_outlet_node_image(self):
        '''Build outlet image.'''
        d = simple_diagram()
        rows = []
        for i, layer in enumerate(d.tree):
            for j, node in enumerate(flatten_layer(layer)):                 #         vv
                if i == 0:                                                  #        0123456789
                    rows.append('')                                         # row 0 ''
                    rows.append(add_node('', label_node(layer[0], 1), 1))   # row 1 ' [O]'
                    rows.append(add_trunk('', 2))                           # row 2 '  |'
                    rows.append(d.add_branches(rows[-1], i, j, node))       # row 3 '  |'
                    rows.append(add_trunks('', rows[-1], ("|", "'")))	    # row 4 '  |'
        self.assertEqual(rows[0], '')
        self.assertEqual(rows[1], ' [O]')
        self.assertEqual(rows[2], '  |')
        self.assertEqual(rows[3], '  |')
        self.assertEqual(rows[4], '  |')

    def test_build_ouetlet_node_image_with_branches(self):
        '''Build outlet image with branches.'''	
        d = complex_diagram()
        rows = []
        for i, layer in enumerate(d.tree):
            for j, node in enumerate(flatten_layer(layer)):
                if i == 0:
                    rows.append('')                                         # row 0 ''
                    rows.append(add_node('', label_node(layer[0], 1), 1))   # row 1 ' [O]'
                    rows.append(add_trunk('', 2))                           # row 2 '  |'
                    rows.append(d.add_branches(rows[-1], i, j))             # row 3 "  |----'"
                    rows.append(add_trunks('', rows[-1], ("|", "'")))	# row 4 '  |    |'
        self.assertEqual(rows[0], '')
        self.assertEqual(rows[1], ' [O]')
        self.assertEqual(rows[2], '  |')
        self.assertEqual(rows[3], "  |----'")
        self.assertEqual(rows[4], '  |    |')

class TestDiagram(unittest.TestCase):
    '''Tests Diagram class.'''
    def test_layer(self):
        '''Test layer method.'''
        d = Diagram(tree=[[Outlet()]])
        self.assertEqual(d.layer(0), [Outlet()])
        with self.assertRaises(ValueError):
            d.layer(1)
        with self.assertRaises(ValueError):
            d.layer(-1)

    def test_add_outlet_simple(self):
        '''Test add outlet method.'''
        d = simple_diagram()
        rows = d.add_outlet(Outlet())
        self.assertEqual(rows, ['', ' [O]', '  |', '  |', '  |'])

    def test_add_outlet_complex(self):
        '''Test add outlet method.'''
        d = Diagram(System(complex_diagram().tree).diagram)
        rows = d.add_outlet(Outlet())
        self.assertEqual(rows, ['', ' [O]', '  |', "  |----'", '  |    |'])

    def test_add_middle_layer_node(self):
        '''Test add middle layer node method.'''
        d = complex_diagram()
        image = d.add_outlet(Outlet())
        rows = d.add_middle_layer_node(d.tree[1][0][0], 1, 1, 0, '', image[-1])
        self.assertEqual(rows[0], ' [S1]')
        self.assertEqual(rows[1], '  |')
        self.assertEqual(rows[2], "  |")
        self.assertEqual(rows[3], "  |")
