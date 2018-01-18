from graph import *

### utils ###

def get_path_str(path):
  str_path = ""
  i = 0
  for node in path:
    if i == len(path)-1:
      str_path += node.name
    else:
      str_path += node.name + "->"
    i = i + 1
  return str_path

def print_network_path_dict(network_symmetric_paths):
  for k,v in network_symmetric_paths.iteritems():
    print "from " + str(k[0].name) + " to " + str(k[1].name) + ": {" + get_path_str(v) + "}"

def print_general_path_list_dict(network_general_path_list):
  for k,v in network_general_path_list.iteritems():
    print "from " + str(k[0].name) + " to " + str(k[1].name)
    for path in v:
      print "      {" + get_path_str(path) + "}"

def copy_path(path):
  path_copy = []
  for node in path:
    path_copy.append(node)
  return path_copy


def print_DAG_queue(queue):
	string_buffer = ""
	for node_name in queue:
		string_buffer = string_buffer + "," + node_name
	return string_buffer
def is_node_in_path(path_str,check_node,graph):
	path = get_path_from_path_str(path_str,graph)
	if path is None:
		return None

	for node in path:
		if node.name == check_node:
			return True
	return False

def get_next_node_in_path(path_str,current_node,graph):
	path = get_path_from_path_str(path_str,graph)
	if path is None:
		return None

	next_node = None
	get_next_node = False
	for node in path:
		if get_next_node == True:
			return node
		if node.name == current_node.name:
			get_next_node = True
	return None


def get_previous_node_in_path(path_str,current_node,graph):
	path = get_path_from_path_str(path_str,graph)
	if path is None:
		return None

	previous_node = None
	for node in path:
		if node.name == current_node.name:
			return previous_node
		previous_node = node
	return None

def get_previous_node_in_path_by_node_name(path_str,current_node_name,graph):
	path = get_path_from_path_str(path_str,graph)
	if path is None:
		return None

	previous_node = None
	for node in path:
		if node.name == current_node_name:
			return previous_node
		previous_node = node
	return None


def get_link_from_to(node1,node2):
	for link in node1.links:
		if link.next_node.name == node2.name:
			return link
	return None
def get_inport_at_switch_from_path(graph_switch,path_str,graph):
	path_found = None
	
	path_found = get_path_from_path_str(path_str,graph)

	if path_found is None:
		return None

	previous_node = None
	for node in path_found:
		if node.name == graph_switch.name:
			break
		previous_node = node

	if previous_node is None:
		return None

	for link in graph_switch.links:
		if link.next_node.name == previous_node.name:
			return link.current_port

	return None

def get_path_from_path_str(path_str,graph):
	path_found = None
	for source_destination,end_to_end_path_list in graph.all_path_list.iteritems():
		if path_found is not None:
			break
		source = source_destination[0]
		destination = source_destination[1]
		for path in end_to_end_path_list:
			if get_path_str(path) == path_str:
				path_found = path
				break
	return path_found

def get_path_index_from_path_string(path_str,graph):
	path_found = None
	path_index = 0
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		if path_found is not None:
			break

		for path in end_to_end_path_list:
			if get_path_str(path) == path_str:
				path_found = path
				break
			path_index = path_index + 1
	return path_index

def get_convergent_node_fast_failover_path(fast_failover_path_str, original_path_str,starting_node_name,graph):
	fast_failover_path = get_path_from_path_str(fast_failover_path_str,graph)
	started = False
	for node_in_ff in fast_failover_path:
		
		if started == True:
			is_convergent = is_node_in_path(original_path_str,node_in_ff.name,graph)
			if is_convergent:
				return node_in_ff.name
		if node_in_ff.name == starting_node_name:
			started = True
	return None


def calculate_number_of_paths(network_general_path_list):
	count = 0
	for k,v in network_general_path_list.iteritems():
		for path in v:
			count = count +1
	return count

def get_all_traffic_weight(path_weights):
	all_traffic_weight = 0
	for weight in path_weights:
		all_traffic_weight += weight
	return all_traffic_weight


def transform_independent_events(r1,r2):
	if r1<r2:
		am = r1*2
		bm = (r1+r2)
	else:
		am = (r1+r2)
		bm = r2*2
	return [am,bm]
