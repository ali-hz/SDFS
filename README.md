Stateful Distributed Firewall aaS (SDFS)
========================================

This repository contains the python proof of concept of SDFS for the connection tracking application.

## Introduction
SDFS for network controllability and management offloads the processing of stateful applications from the control-plane to the data-plane and optimizes a distributed stateful application in the data-plane to transform the SDN network into a one big firewall. While maintaining modularity of the framework, SDFS offers an optimized processing burden distribution of the stateful application in the data-plane among the switches in the network with inherent fault-tolerance mechanisms that eliminate the need for immediate controller intervention even in cases of failure or attacks on the network.

## Features
- Abstracts the network into one big firewall at the management plane
- Uses an intelligent algorithm to distribute and balance the burden of stateful firewall processing over multiple switches in the network
- Accounts for weighted paths and network element capacities through a cost-capacity-aware optimization.
- Relaxes the constraints on requiring path information in the network
- Maintains modularity: independently plugged into the controller without disrupting other applications
- Inherently implements fault-tolerance mechanisms that bring forth an application with High Availability
- Yields a controllable stateful application in the data-plane with minimal controller intervention

## Environment Requirmeents
This engine is designed to be used with openVswitch and mininet. Here are the requirements
- Linux Kernel Version: 3.10 to 4.12
- OpenVswitch version: 2.8.90. http://openvswitch.org/
- Mininet version: 2.2.1. http://mininet.org/

## Setup Instructions
- Fork and then clone the repo or download the .zip file
- Install python dependencies (list to be added)

## Demo

### Topology
Example mininet topologies are added in the topologies folder. Along with the defined topology class, a topo object must contain the following attributes:
- protected_hosts: list of hosts to be protected in the connection tracking example.
- routes: a dictionary that contains the routes in the network. Although routes can be discovered automatically, this attribute is used by the user to explicitly set the routes and inspect the state distribution behavior.
- ff_paths: a dictionary that contains the fast-failover routes in the network.

### SDFS Configuration
The config.xml file contains the global configuration of the application.
- topo-name: The name of the topology
- routing: The routing behavior employed in the network. Can be "L3" or "L4".
- path-aggregariton: If the network employs "L4" routing, a path-aggregation mechanism must be defined. Can be "PAA" or "AAC"
- use-fast-failover: Allow packets to be redirected according to the ff_paths dictionary in the topology upon switch-port failure events.

Template configurations are provided in "example-config" folder.

### Running the POC
Spwan the topology:
```
python fire_network.py
```
Establish SDFS in network:
```
python fire_SDFS.py
```

### Inspecting Behavior
Use iperf tool in mininet to establish many connections between the protected hosts and the other hosts.
Check which switch are processing the connection tracking states in the data-plane on the path of the packets. Connections being processed at any switch are reresented in OF-table 20:
```
ovs-ofctl dump-flows -O OpenFlow15 $switch-name | grep "table=20, n_packets"
```
TODO: Automated testing scripts will be added
