# Lattice

The lattice Python package is used to model systems of reservoirs and their operations.

### Installation

The lattice package Python dependencies are managed using Poetry. Installing poetry makes installing lattice and its dependencies straightforward. First, if you haven't already first install Python. Next, to install Poetry follow the instructions here: https://python-poetry.org/docs/#installing-with-the-official-installer. Then, clone or fork the respository located on Github: https://github.com/JohnRushKucharski/lattice. Finally, from the directory containing the local repository, using your favorite terminal or shell run:

```
poetry install
```

### Design

lattice models systems of reservoirs, and related elements. These **systems** are composed of **node**s. At a minimum, these systems must include at least one upstream-most **inflow** node and one downstream-most **outlet** node, which together define the system's boundary conditions.

#### Simple Diagram
A user provided list of nodes, describe the configuration of a system. The following list describes a simple system composed of one *storage* node, and the pre-requisite up and downstream boundary nodes.

```
simple_diagram = [
    [Outlet()],
    [Storage(reservoir=BasicReservoir())],
    [Inflow([1, 1, 0])]
]
```

The inflow node is constructed with the provided timeseries of flows (i.e. [1, 1, 0]) and other unspecified default parameters. The storage node is constructed from a default basic reservoir with default parameters including and initial storage value of 0 and capacity of 1. The default basic reservoir operations are passive, meaning releases are only made when the reservoir exceeds its capacity. The simulation of this system would produce the following results:

- inflow_node: $I_t$ = [1, 1, 0] 

where $I_t$ is the provided timeseries of inflows.

- storage_node: $S_t(I_t, V_t, (O_{i,t}))$ = [(0, 0, (0,)), (1, 1, (0,)), (1, 1, (1,)), (0, 1, (0,))] 

where $I_t$ are reservoir (and storage node) inflows, $V_t$ is the storage volume of the reservoir at the end to timestep $t$, and $O_{i,t}$ are outflows from the storage node through reservoir outlet $i$ at timestep, $t$. 

*Note: Storage volumes are updated via the operations function. In this particular case, $V_t = V_{t-1} + I_t - O_t$, where $O_t = max(V_{t-1} + I_t - K, 0)$ and K is the capacity of the storage node reservoir (in this case: $K = 1$).*      

- outlet_node: $O_t$ = [0, 1, 0]

where $O_t$ is the timeseries of outflows leaving the system.

#### Complex diagram

An example of a more complex system diagram is shown below:

```
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
```

This diagram represents the following system schematic with annotated with the expected simulation values from such a system:

```
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
```


