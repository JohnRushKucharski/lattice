'''Tests node.py'''
import unittest

from lattice.node import Log, Inflow

class TestLog(unittest.TestCase):
    '''Tests Log class.'''
    def test_record_inflow(self):
        '''Test record method.'''
        inflow = Inflow(data=[1, 2, 3])
        log = inflow.attach_log(Log())
        self.assertEqual(log.records, [])
        inflow.send()
        self.assertEqual(log.records, [(1, 1)])
        inflow.send()
        self.assertEqual(log.records, [(1, 1), (2, 2)])
        inflow.send()
        self.assertEqual(log.records, [(1, 1), (2, 2), (3, 3)])
    def test_record_by_label(self):
        '''Test record method.'''
        inflow = Inflow(data=[1, 2, 3])
        log = inflow.attach_log(Log())
        inflow.send()
        inflow.send()
        inflow.send()
        self.assertEqual(log.records_by_label('inflow'), [1, 2, 3])
        self.assertEqual(log.records_by_label('outflow'), [1, 2, 3])

class TestInflow(unittest.TestCase):
    '''Tests Inflow class.'''
    def test_receive(self):
        '''Test receive method.'''
        inflow = Inflow(data=[1, 2, 3])
        self.assertEqual(inflow.receive(), 1)
        self.assertEqual(inflow.receive(), 2)
        self.assertEqual(inflow.receive(), 3)
