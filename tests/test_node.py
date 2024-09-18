'''Tests node.py'''
import unittest

from lattice.node import Inflow

class TestInflow(unittest.TestCase):
    '''Tests Inflow class.'''
    def test_receive(self):
        '''Test receive method.'''
        inflow = Inflow([1, 2, 3])
        self.assertEqual(inflow.receive(), 1)
        self.assertEqual(inflow.receive(), 2)
        self.assertEqual(inflow.receive(), 3)
