from __future__ import division
from copy import copy
import math
import numpy
import random
from graph import *
import pprint
pp = pprint.PrettyPrinter(indent=4)
from utils import *
import time


def calculate_path_explicit_cumulatives(variables, switch_index,graph):
	""" returns the matrix of cumulative values
	"""
	network_general_path_list = graph.network_general_path_list
	cumulative_variables = copy(variables)
	path_index = 0
	for end_to_end,end_to_end_path_list in network_general_path_list.iteritems():
		for path in end_to_end_path_list:
			cumulative = 0
			for node in path:
				if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
					if switch_index.get(node.name) is not None:
						cumulative = cumulative + variables[switch_index.get(node.name)][path_index]
						cumulative_variables[switch_index.get(node.name)][path_index] = cumulative
			path_index = path_index + 1
	return cumulative_variables

def generate_path_to_burden_map_per_node(variables, switch_index,graph):
	""" maps the values obtained in the optimization into the graph switches in a dictionary: path_to_burden_map
	"""
	path_index = 0
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		source = source_destination[0]
		destination = source_destination[1]
		for path in end_to_end_path_list:
			for node in path:
				if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
					if switch_index.get(node.name) is not None:
						graph_switch = graph.get_node(node.name)
						if graph_switch is not None:
							burden = variables[switch_index.get(node.name)][path_index]
							if graph_switch.param_dict.get("path_to_burden_map") is None:
								graph_switch.param_dict["path_to_burden_map"] = dict()
							
							if graph_switch.param_dict["path_to_burden_map"].get((source.name,destination.name)) is None:
								graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)] = dict()
							
							if graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)].get(get_path_str(path)) is None:
								graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)][get_path_str(path)] = dict()
							graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)][get_path_str(path)]["burden"] = burden
			path_index = path_index + 1


def generate_cumulative_burden_values_in_map_per_node(variables, switch_index,graph,path_weights):
	""" maps the cumulative values of the optimization results into the graph switches in a dictionary: path_to_burden_map
	"""
	path_index = 0
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		source = source_destination[0]
		destination = source_destination[1]
		for path in end_to_end_path_list:
			cumulative = 0
			for node in path:
				if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
					if switch_index.get(node.name) is not None:
						graph_switch = graph.get_node(node.name)
						if graph_switch is not None:
							burden = None
							try:
								burden = graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)][get_path_str(path)]["burden"]
							except Exception,e:
								print e
								print "Exception, cannot find burden in switch: " + graph_switch.name + " for path: " + get_path_str(path)
							if burden is not None:
								cumulative = cumulative + burden
								graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)][get_path_str(path)]["cumulative_burden_per_path"] = cumulative
								graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)][get_path_str(path)]["cumulative_burden_per_path_percentage"] = cumulative/path_weights[path_index]
								graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)][get_path_str(path)]["inport"] = get_inport_at_switch_from_path(graph_switch,get_path_str(path),graph)

			path_index = path_index + 1


def generate_asserted_cumulatives(variables, switch_index,graph,path_weights):
	""" generates cumulative values based on the CAA approach for L4-LB networks
	"""

	# prepare dictionaries in graph switches
	for node in graph.nodes:
		if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
			graph_switch = node

			try:
				graph_switch.param_dict["path_to_burden_map"]
			except Exception, e:
				print "cannot find source destination map"
				continue

			for source_destination,paths in graph_switch.param_dict["path_to_burden_map"].iteritems():
				

				if graph_switch.param_dict.get("asserted_cumulatives_params") is None:
					graph_switch.param_dict["asserted_cumulatives_params"] = dict()
				if graph_switch.param_dict["asserted_cumulatives_params"].get(source_destination) is None:
					graph_switch.param_dict["asserted_cumulatives_params"][source_destination] = dict()
				if graph_switch.param_dict["asserted_cumulatives_params"][source_destination].get("path_identifier") is None:
					graph_switch.param_dict["asserted_cumulatives_params"][source_destination]["path_identifier"] = dict()

				for path_str,path_params in paths.iteritems():
					inport = None
					if path_params.get("inport") is not None:
						inport = copy(path_params.get("inport"))
					if inport is None:
						continue
					if graph_switch.param_dict["asserted_cumulatives_params"][source_destination]["path_identifier"].get(inport) is None:
						graph_switch.param_dict["asserted_cumulatives_params"][source_destination]["path_identifier"][inport] = dict()
					if graph_switch.param_dict["asserted_cumulatives_params"][source_destination]["path_identifier"][inport].get("path_list_group") is None:
						graph_switch.param_dict["asserted_cumulatives_params"][source_destination]["path_identifier"][inport]["path_list_group"] = []

					graph_switch.param_dict["asserted_cumulatives_params"][source_destination]["path_identifier"][inport]["path_list_group"].append(path_str)




	source_destination_list = []
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		if source_destination not in source_destination_list:
			source_destination_list.append(source_destination)
	
		# generate parent dict
		parent_dict = dict()
		for path in end_to_end_path_list:
			for node in path:

				if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
					if previous_node is not None:
						if parent_dict.get(node.name) is None:
							parent_dict[node.name] = []
						if previous_node.name not in parent_dict[node.name]:
							parent_dict[node.name].append(previous_node.name)
				previous_node = node

		# generate same level dict
		same_level_dict = dict()
		for parent_node,parent_node_children in parent_dict.iteritems():
			for child_node in parent_node_children:
				same_level_for_child = []
				same_level_for_child.extend(parent_node_children)
				for other_parent_node,other_parent_node_children in parent_dict.iteritems():
					if child_node in other_parent_node_children:
						same_level_for_child.extend(other_parent_node_children)
				same_level_for_child_set = set(same_level_for_child)
				same_level_dict[child_node] = same_level_for_child_set
		


		source = source_destination[0]
		destination = source_destination[1]
		source_destination_names = (source.name,destination.name)
		current_node = None
		next_node = None
		

		calculated = []
		taken_nodes = []

		taken_nodes.append(source.name)
		taken_nodes.append(destination.name)

		# get first switch
		for link in destination.links:
			current_node = link.next_node

		


		for source_destination_asserted, source_destination_dict in current_node.param_dict["asserted_cumulatives_params"].iteritems():
			if source_destination_asserted[0] == source.name and source_destination_asserted[1] == destination.name:
				pass
			else:
				continue


			weighted_path_cumulatives_sum = 0
			relevant_path_weight_sum = 0
			max_weight = 0
			for inport, inport_dict in source_destination_dict["path_identifier"].iteritems():

				for path_str in inport_dict["path_list_group"]:
					path_index = get_path_index_from_path_string(path_str,graph)

					cumulative_burden = current_node.param_dict["path_to_burden_map"][source_destination_asserted][path_str]["cumulative_burden_per_path"]
					weighted_path_cumulatives_sum = weighted_path_cumulatives_sum + cumulative_burden*path_weights[path_index]
					relevant_path_weight_sum = relevant_path_weight_sum + path_weights[path_index]
					max_weight = max_weight + path_weights[path_index]*path_weights[path_index]
			max_weight_average = max_weight/(relevant_path_weight_sum)
			asserted_cumulative_average = weighted_path_cumulatives_sum/(relevant_path_weight_sum)
			current_node.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_cumulative"] = asserted_cumulative_average
			current_node.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_cumulative_percentage"] = asserted_cumulative_average/max_weight_average		


		taken_nodes.append(current_node.name)
		calculated.append(current_node.name)

		in_queue = []
		in_queue.append(current_node)

		while len(in_queue)>0:
		#for i in range(0,10):
			current_node = in_queue[0]
			if len(in_queue)>1:
				in_queue = in_queue[1:]
			else:
				in_queue = []

			for link in current_node.links:
				viable_next_node = link.next_node
				
				if viable_next_node.name in taken_nodes:
					continue
				if viable_next_node.name not in same_level_dict.keys():
					continue
				
				asserted_cumulative_average = 0
				max_weight_average = 0
				weighted_path_cumulatives_sum = 0
				relevant_path_weight_sum = 0
				max_weight = 0
				# calculating average
				for same_level_node in same_level_dict[viable_next_node.name]:

					if same_level_node not in calculated:
						same_level_node_object = graph.get_node(same_level_node)
						for source_destination_asserted, source_destination_dict in same_level_node_object.param_dict["asserted_cumulatives_params"].iteritems():
							if source_destination_asserted[0] == source.name and source_destination_asserted[1] == destination.name:
								pass
							else:
								continue
							
							for inport, inport_dict in source_destination_dict["path_identifier"].iteritems():

								for path_str in inport_dict["path_list_group"]:
									path_index = get_path_index_from_path_string(path_str,graph)

									cumulative_burden = same_level_node_object.param_dict["path_to_burden_map"][source_destination_asserted][path_str]["cumulative_burden_per_path"]
									weighted_path_cumulatives_sum = weighted_path_cumulatives_sum + cumulative_burden*path_weights[path_index]
									relevant_path_weight_sum = relevant_path_weight_sum + path_weights[path_index]
									max_weight = max_weight + path_weights[path_index]*path_weights[path_index]
				
				for same_level_node in same_level_dict[viable_next_node.name]:
					if same_level_node not in calculated:
						max_weight_average = max_weight/(relevant_path_weight_sum)
						asserted_cumulative_average = weighted_path_cumulatives_sum/(relevant_path_weight_sum)
								
						same_level_node_object = graph.get_node(same_level_node)
						same_level_node_object.param_dict["asserted_cumulatives_params"][source_destination_names]["asserted_additive_cumulative"] = asserted_cumulative_average
						same_level_node_object.param_dict["asserted_cumulatives_params"][source_destination_names]["asserted_additive_cumulative_percentage"] = asserted_cumulative_average/max_weight_average		
						
						calculated.append(same_level_node)

				if viable_next_node not in in_queue:
					in_queue.append(viable_next_node)

			taken_nodes.append(current_node.name)

	# calculating the speculative aggregate burden of a switch, assuming it is subjected to this approach
	for source_destination_general,end_to_end_path_list in graph.network_general_path_list.iteritems():
			for path in end_to_end_path_list:
				for node in path:
					if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
						graph_switch = node
						for source_destination_asserted, source_destination_dict in graph_switch.param_dict["asserted_cumulatives_params"].iteritems():

							if source_destination_asserted[0] == source_destination_general[0].name and source_destination_asserted[1] == source_destination_general[1].name:
								for inport, inport_dict in source_destination_dict["path_identifier"].iteritems():

									current_percentage = source_destination_dict["asserted_additive_cumulative_percentage"]
									for path_str in inport_dict["path_list_group"]:
										if get_path_str(path) == path_str:

											path_index = get_path_index_from_path_string(path_str,graph)
											if path_index is not None:

												prev_node_for_path = get_previous_node_in_path(path_str,graph_switch,graph)
												if prev_node_for_path.name == previous_node.name:
													if previous_node.param_dict.get("asserted_cumulatives_params") is not None:

														prevoius_percentage = previous_node.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_cumulative_percentage"]
														for inport_prevoius, inport_dict_previous in previous_node.param_dict["asserted_cumulatives_params"][source_destination_asserted]["path_identifier"].iteritems():
															for prev_path_str in inport_dict_previous["path_list_group"]:
																if prev_path_str == path_str:
																	path_index = get_path_index_from_path_string(path_str,graph)
																	weight_of_path = path_weights[path_index]
																	assumed_marginal_aggregate_weight = (current_percentage - prevoius_percentage)*weight_of_path
																	if graph_switch.param_dict["asserted_cumulatives_params"][source_destination_asserted].get("asserted_additive_aggregate") is None:
																		graph_switch.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_aggregate"] = 0
																	graph_switch.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_aggregate"] = graph_switch.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_aggregate"] + assumed_marginal_aggregate_weight
					

													else:
														for path_str_inside in inport_dict["path_list_group"]:
															if path_str_inside == path_str:
																path_index = get_path_index_from_path_string(path_str_inside,graph)
																if path_index is not None:
																	weight_of_path = path_weights[path_index]
																	assumed_marginal_aggregate_weight = current_percentage*weight_of_path
																	if graph_switch.param_dict["asserted_cumulatives_params"][source_destination_asserted].get("asserted_additive_aggregate") is None:
																		graph_switch.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_aggregate"] = 0
																	graph_switch.param_dict["asserted_cumulatives_params"][source_destination_asserted]["asserted_additive_aggregate"] += assumed_marginal_aggregate_weight




					previous_node = node



def generate_cumulative_aggregate_weights(variables, switch_index,graph,path_weights):
	""" generates cumulative values based on the PAA approach for L4-LB networks
	"""

	all_traffic_weight = get_all_traffic_weight(path_weights)
	
	source_destination_list = []
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		if source_destination not in source_destination_list:
			source_destination_list.append(source_destination)
	
	for source_destination in source_destination_list:
		
		aggregate_weights = get_source_destination_aggregate_variables(graph, variables,source_destination,switch_index)

		aggregate_source_destination_traffic_weight = get_aggregate_source_destination_traffic_weight(graph,path_weights,source_destination)

		source = source_destination[0]
		destination = source_destination[1]
		current_node = None
		next_node = None
		# get first switch
		for link in source.links:
			current_node = link.next_node

		HCW_dict = dict()
		queue = []
		queue.append(current_node.name)

		end_to_end_path_list = graph.network_general_path_list[source_destination]
		
		path_traversal_dict = dict()
		for path in end_to_end_path_list:
			path_traversal_dict[get_path_str(path)] = get_next_node_in_path(get_path_str(path),current_node,graph).name
				

		
		i = 0
		while queue[len(queue)-1] != destination.name:
			if i >40:
				print "Error in QUEUE!"
				break

			for path_str,next_path_node in path_traversal_dict.iteritems():
				next_path_node_object = graph.get_node(next_path_node)
				look_for_another = False
				if next_path_node in queue:
					if get_next_node_in_path(path_str,next_path_node_object,graph) != None:
						path_traversal_dict[path_str] = get_next_node_in_path(path_str,next_path_node_object,graph).name
					continue

				for compare_path in end_to_end_path_list:
					if get_path_str(compare_path) == path_str:
						continue
					if is_node_in_path(get_path_str(compare_path),next_path_node,graph):
						if next_path_node == path_traversal_dict[get_path_str(compare_path)]:
							pass
						else:
							look_for_another = True
							break
				if not look_for_another:
					if get_next_node_in_path(path_str,next_path_node_object,graph) != None:
						path_traversal_dict[path_str] = get_next_node_in_path(path_str,next_path_node_object,graph).name
					queue.append(next_path_node)
			i = i + 1

		

		node_incr_in_queue = 0
		for node_name in queue:

			node = graph.get_node(node_name)
			if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
					
				

				graph_switch = node
				# 1 for (starting with 0), 1 for end host
				if node_incr_in_queue == len(queue)-2:
					if graph_switch.param_dict.get("cumulative_aggregate_weight_map") is None:
						graph_switch.param_dict["cumulative_aggregate_weight_map"] = dict()
					if graph_switch.param_dict["cumulative_aggregate_weight_map"].get((source.name,destination.name)) is None:
						graph_switch.param_dict["cumulative_aggregate_weight_map"][(source.name,destination.name)] = dict()
						
					graph_switch.param_dict["cumulative_aggregate_weight_map"][(source.name,destination.name)]["cumulative_aggregate_weight"] = aggregate_source_destination_traffic_weight
					graph_switch.param_dict["cumulative_aggregate_weight_map"][(source.name,destination.name)]["cumulative_aggregate_sum_path_weight"] = aggregate_source_destination_traffic_weight
					continue


				must_repeat = True
				list_disregarded_paths = []

				if HCW_dict.get((source.name,destination.name)) is None:
						HCW_dict[(source.name,destination.name)] = dict()

				path_to_burden_dict = graph_switch.param_dict["path_to_burden_map"][(source.name,destination.name)]
				for path,path_burden in path_to_burden_dict.iteritems():
					if HCW_dict.get((source.name,destination.name)).get(path) is None:
						HCW_dict[(source.name,destination.name)][path] = 0


				
				while (must_repeat):
					must_repeat = False

					cum_aggregate_sub = aggregate_weights[switch_index[graph_switch.name]]*aggregate_source_destination_traffic_weight

					sum_of_taken_paths = 0
					
					
					for path,path_burden in path_to_burden_dict.iteritems():
						if path in list_disregarded_paths:
							continue

						path_index = get_path_index_from_path_string(path,graph)
						
						cum_aggregate_sub += HCW_dict[(source.name,destination.name)][path]*path_weights[path_index]
						sum_of_taken_paths += path_weights[path_index]

					cum_aggregate = cum_aggregate_sub/sum_of_taken_paths
					if cum_aggregate>aggregate_source_destination_traffic_weight:
						cum_aggregate = aggregate_source_destination_traffic_weight
					
					for path,path_burden in path_to_burden_dict.iteritems():
						if path in list_disregarded_paths:
							continue
						if cum_aggregate<HCW_dict[(source.name,destination.name)][path]:
							list_disregarded_paths.append(path)
							must_repeat = True
				
				for path,path_burden in path_to_burden_dict.iteritems():

					if path in list_disregarded_paths:
						continue
					if cum_aggregate>HCW_dict[(source.name,destination.name)][path]:
						HCW_dict[(source.name,destination.name)][path] = cum_aggregate
			

				if graph_switch.param_dict.get("cumulative_aggregate_weight_map") is None:
					graph_switch.param_dict["cumulative_aggregate_weight_map"] = dict()
				if graph_switch.param_dict["cumulative_aggregate_weight_map"].get((source.name,destination.name)) is None:
					graph_switch.param_dict["cumulative_aggregate_weight_map"][(source.name,destination.name)] = dict()
					
				graph_switch.param_dict["cumulative_aggregate_weight_map"][(source.name,destination.name)]["cumulative_aggregate_weight"] = cum_aggregate
				graph_switch.param_dict["cumulative_aggregate_weight_map"][(source.name,destination.name)]["cumulative_aggregate_sum_path_weight"] = aggregate_source_destination_traffic_weight

			node_incr_in_queue = node_incr_in_queue + 1


	# for node in graph.nodes:
 # 		if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
 # 			graph_switch = node
 # 			if graph_switch.param_dict.get("path_to_burden_map") is not None:
 # 				print "at switch: " + graph_switch.name
 # 				pp.pprint(graph_switch.param_dict["cumulative_aggregate_weight_map"])


def get_aggregate_source_destination_traffic_weight(graph,path_weights,source_destination):
	""" Sums all traffic weight required for a source-destination pair
	"""
	aggregate_path_weight = 0
	source = source_destination[0]
	destination = source_destination[1]

	path_incr = 0
	for found_source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		found_source = found_source_destination[0]
		found_destination = found_source_destination[1]
		for path in end_to_end_path_list:
			if found_source.name == source.name and found_destination.name == destination.name:
				aggregate_path_weight += path_weights[path_incr]
			path_incr = path_incr + 1
	return aggregate_path_weight

		



def get_source_destination_aggregate_variables(graph, variables,source_destination,switch_index):
	""" returns vector of size switches. Each element represents the sum of processing burden of a switch corresponding to a source-destination pair
	"""

	number_of_switches = len(variables)
	number_of_paths = len(variables[0])

	source = source_destination[0]
	destination = source_destination[1]

	list_of_path_indeces = []

	path_incr = 0
	for found_source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		found_source = found_source_destination[0]
		found_destination = found_source_destination[1]
		for path in end_to_end_path_list:
			if found_source.name == source.name and found_destination.name == destination.name:
				list_of_path_indeces.append(path_incr)
			path_incr = path_incr + 1

	aggregate_weights = numpy.zeros((number_of_switches,1))

	for i in range(0,len(variables)):
		for j in range(0,len(variables[0])):
			if j in list_of_path_indeces:
				aggregate_weights[i][0] = aggregate_weights[i][0] + variables[i][j]
	return aggregate_weights






















