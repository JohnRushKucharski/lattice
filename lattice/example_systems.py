'''
A few example systems for testing and demonstration purposes.
'''

from lattice.reservoir import BasicReservoir
from lattice.node import Inflow, Storage, Outlet, Log


simple_diagram = [
    [Outlet(log=Log())],
    [Storage(reservoir=BasicReservoir(), log=Log())],
    [Inflow([1, 1, 0], log=Log())]
]
# expected outflow at simple_diagram outlet = [0, 1, 0]


complex_diagram = [
    [Outlet(log=Log())],
    [ # layer 1
        Storage(BasicReservoir(), name='storage1', log=Log()),
        Storage(BasicReservoir(), name='storage2', log=Log())
    ],
    [ # layer 2
        Inflow([1, 1, 0], name='inflow1', log=Log()),
        [ # group of nodes in layer 2
            Storage(BasicReservoir(capacity=2), name='storage3', log=Log()),
            Storage(BasicReservoir(capacity=2), name='storage4', log=Log())
        ]
    ],
    [Inflow([1, 1, 1], name='inflow2', log=Log()), Inflow([1, 1, 1], name='inflow3', log=Log())]
]
# expected outflow at complex diagram outlet = [0, 1, 1]
