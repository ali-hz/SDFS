import commands
#from topo import *
from collections import defaultdict
from utils import *
import numpy
import networkx as nx
from engine import *
from utils import *
from optimizer import *




class Link:
  def __init__(self,current_port, next_node,next_port):
    self.current_port = current_port
    self.next_node = next_node
    self.next_port = next_port

class Node:
  def __init__(self, name,node_type):
    self.name = name
    self.node_type = node_type
    self.links = []
    self.param_dict = dict()


class Graph:
  def __init__(self):
    self.nodes = set()
    self.topo = None
    self.routing = None
    self.switches = []
    self.network_symmetric_paths = dict()
    self.network_general_path_list = dict()
    self.all_path_list = dict()
    self.locked_hosts = []
    self.switch_index = None
    self.path_weights = None
    self.capacity_vector = None
    self.variables = None
    self.switches_to_nullify = []
    

    
  def populate(self,topo,routing):
    # TODO: check if instance of topo
    if topo is None:
      return False
    if routing is None:
      return False

    self.topo = topo
    self.routing = routing

    if self.topo.routes.get(self.routing) is None:
      print "Error: Configured routing, " + str(routing) + ", behavior is not supported by topology"
      return False

    try:
      self.locked_hosts =self.topo.protected_hosts
    except:
      print "Error: No protected hosts defined in the topology"
      return False

    self.switches_to_nullify = []
    try:
      self.switches_to_nullify = self.topo.switches_to_nullify
    except:
      pass

    self.ff_paths = dict()
    try:
      self.ff_paths = self.topo.ff_paths
    except:
      pass

    self.__construct_graph__()
    self.populate_switches()
    #self.generate_end_to_end_paths()
    self.generate_general_end_to_end_path_list()


    # assert single route for source destination
    if self.routing == "L3":
      inconsistent_paths_with_routing = False
      for source_destination,end_to_end_path_list in self.network_general_path_list.iteritems():
        if len(end_to_end_path_list)!= 1:
          print "Error: no single route for source destination: " + str(source_destination[0].name + "," + source_destination[1].name) + " using L3-routing"
          inconsistent_paths_with_routing = True
      if inconsistent_paths_with_routing:
        return

    self.generate_switch_path_matrix()
    self.generate_path_weight_vector()
    self.generate_capacity_vector()
    self.get_tracking_weights()

    return True
  def get_node(self,node_name):
    for node in self.nodes:
      if node.name == node_name:
        return node
    return None
  def add_node(self, node):
    self.nodes.add(node)

  def add_edge(self, node1,current_port,next_node,next_port):
    link1 = Link(current_port,next_node,next_port)
    node1.links.append(link1)

    link2 = Link(next_port,node1,current_port)
    next_node.links.append(link2)


  def add_nodes_from_link(self,node1_name,node2_name):
    # add nodes to graph
    node1_found = False
    node2_found = False
    for node in self.nodes:
      if node1_found and node2_found:
        break
      if node1_name == node.name:
        node1_found = True
      if node2_name == node.name:
        node2_found = True

    if not node1_found:
      if node1_name[0] == "s":
        node1 = Node(node1_name,"switch")
      else:
        node1 = Node(node1_name,"host")
      self.add_node(node1)

    if not node2_found:
      if node2_name[0] == "s":
        node2 = Node(node2_name,"switch")
      else:
        node2 = Node(node2_name,"host")
      self.add_node(node2)

  def populate_switches(self):
    for node in self.nodes:
      if self.topo.nodeInfo(node.name).get("isSwitch") is not None and self.topo.nodeInfo(node.name).get("isSwitch") is True:
        self.switches.append(node)
      

  def __construct_graph__(self):
    G=nx.Graph()

    topo = self.topo
    for link in topo.links():
      node1_name = link[0]
      node2_name = link[1]
      ports = topo.port(node1_name,node2_name)
      node1_port = ports[0]
      node2_port = ports[1]

      G.add_edge(node1_name,node2_name)
      self.add_nodes_from_link(node1_name,node2_name)


      node1 = self.get_node(node1_name)
      node2 = self.get_node(node2_name)

      self.add_edge(node1,node1_port, node2,node2_port)

  def generate_general_end_to_end_path_list(self):
    # get host_nodes
    hosts = []
    for node in self.nodes:
      if node.name in self.topo.hosts():
        hosts.append(node)


    # generate paths
    network_paths = []
    for from_host in hosts:
      paths = [[from_host]]
      for path in paths:
        last_node_in_path = path[len(path)-1]
        for link in last_node_in_path.links:
          if link.next_node in path:
            pass
          else:
            new_path = copy_path(path)
            new_path.append(link.next_node)
            paths.append(new_path)

            if new_path[len(new_path)-1] in hosts:
              network_paths.append(new_path)

    # assert symmetric
    network_all_path_list_dict = dict()
    network_general_path_list_dict = dict()
    for network_path in network_paths:
      # make sure one of the hosts is locked
      
      if network_all_path_list_dict.get((network_path[0],network_path[len(network_path)-1])) is None:
          network_all_path_list_dict[(network_path[0],network_path[len(network_path)-1])] = []
      network_all_path_list_dict[(network_path[0],network_path[len(network_path)-1])].append(network_path)


      if not self.xor_locked_host(network_path[0].name,network_path[len(network_path)-1].name):
        continue


      if get_path_str(network_path) in self.topo.routes[self.routing]:
        if network_general_path_list_dict.get((network_path[0],network_path[len(network_path)-1])) is None:
          network_general_path_list_dict[(network_path[0],network_path[len(network_path)-1])] = []
        network_general_path_list_dict[(network_path[0],network_path[len(network_path)-1])].append(network_path)

    self.all_path_list = network_all_path_list_dict
    self.network_general_path_list = network_general_path_list_dict
      
  def xor_locked_host(self,host1_name,host2_name):
    if (host1_name in self.locked_hosts and host2_name not in self.locked_hosts):
      return True
    else:
      return False

  def generate_switch_path_matrix(self):
    graph = self

    switch_index = dict()
    i = 0
    for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
      for path in end_to_end_path_list:
        source = source_destination[0]
        destination = source_destination[1]
        for node in path:
          if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
            if switch_index.get(node.name) is None:
              switch_index[node.name] = i
              i = i + 1
    

    number_of_paths = calculate_number_of_paths(graph.network_general_path_list)
    number_of_switches = len(switch_index)
    variables = numpy.zeros((number_of_switches, number_of_paths))

    path_itr = 0
    for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
      for path in end_to_end_path_list:
        for switch in path:
          if switch.name in switch_index:
            variables[switch_index[switch.name]][path_itr] = 1
        path_itr = path_itr + 1
    
    self.variables = variables
    self.switch_index = switch_index



  def generate_path_weight_vector(self):
    graph = self

    path_info = self.topo.routes[self.routing]
    path_weights = []

    for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
      for path in end_to_end_path_list:
        path_str = get_path_str(path)
        weight = 1000
        if path_str in path_info:
          path_info_dict = path_info.get(path_str)
          if path_info_dict.get("weight") is not None:
            weight = path_info_dict.get("weight")
          else:
            pass
        else:
          pass

        path_weights.append(weight)

    self.path_weights = path_weights


  def generate_capacity_vector(self):
    #{'s8': 4, 's3': 6, 's2': 5, 's1': 0, 's7': 3, 's6': 2, 's5': 1, 's4': 7}

    #return [40,10000, 10000, 10000, 70, 10000, 60, 10000]

    switch_index = self.switch_index
    capacity_vector = []
    #{'s9': 2, 's8': 11, 's3': 7, 's2': 4, 's11': 3, 's10': 9, 's7': 8, 's6': 5, 's5': 1, 's4': 10, 's12': 6, 's1': 0}

    for switch,index in switch_index.iteritems():
        capacity_vector.append(10000)
    self.capacity_vector = capacity_vector

  def get_tracking_weights(self):
    self.variables = optimize(False,self)

