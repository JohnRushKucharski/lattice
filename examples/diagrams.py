'''
A few example systems for testing and demonstration purposes.
'''

from lattice.reservoir import BasicReservoir
from lattice.node import Inflow, Storage, Outlet


simple_diagram = [
    [Outlet()],
    [Storage(reservoir=BasicReservoir())],
    [Inflow([1, 1, 0])]
]
'''
Simple diagram expected simulation values at:
- inflow_node: [1, 1, 0]
- storage_node: [(0, 0, (0,)), (1, 1, (0,)), (1, 1, (1,)), (0, 1, (0,))]
- outlet_node: [0, 1, 0]
'''

complex_diagram = [
    [Outlet()],
    [ # layer 1
        [ # all nodes in layer 1 are grouped (all send to outlet)
        Storage(BasicReservoir()),
        Storage(BasicReservoir())
        ]
    ],
    [ # layer 2
        Inflow([1, 1, 0]),
        [ # group of nodes in layer 2
            Storage(BasicReservoir()),
            Storage(BasicReservoir())
        ]
    ],
    [Inflow([1, 1, 1]), Inflow([1, 1, 1])]
]
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
