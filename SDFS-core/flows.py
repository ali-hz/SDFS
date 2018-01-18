from graph import *
import commands
from engine import *
from utils import *
#from topo import *
#from config import *
import time

# TODO, receiving double packet at initiator
start = time.time()

HARD_TIMEOUT="50"


def delete_all_flows(graph):
	""" delete all flows on switches
	"""
	for switch in graph.switches:
		print commands.getoutput("ovs-ofctl -O OpenFlow15 del-flows " + switch.name + " \"\"")

def delete_all_groups(graph):
	""" delete all groups on switches
	"""
	for switch in graph.switches:
		print commands.getoutput("ovs-ofctl -O OpenFlow15 del-groups " + switch.name + " \"\"")




def table_0(graph):
	""" table 0, install default resubmit to table 7
	"""
	for switch in graph.switches:
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " + switch.name + " \"table=0, priority=10, action=resubmit(,7)\"")



def install_default_arp_forwarding(graph):
	""" table 0, install default arp forwarding
	"""
	path_index = 0
	previous_node = None
	unique_end_to_end_path = None
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		
		source = source_destination[0]
		destination = source_destination[1]

		host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
		host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]



		if len(end_to_end_path_list)>0:
			unique_end_to_end_path = end_to_end_path_list[0]
		else:
			continue

		for node in unique_end_to_end_path:
			graph_switch = node
			current_port = None
			next_port = None

			if graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is not None and graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is True:
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +graph_switch.name + " \"table=0,arp, actions=resubmit(,1)" + "\"")

			if previous_node is None:
				previous_node = node
				continue

			for link in graph_switch.links:
				if link.next_node is None:
					continue

				if link.next_node.name == previous_node.name:
					current_port = link.current_port
					next_port = link.next_port


			if graph.topo.nodeInfo(previous_node.name).get("isSwitch") is not None and graph.topo.nodeInfo(previous_node.name).get("isSwitch") is True:
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +previous_node.name + " \"table=1,arp, arp_spa="+host_ip_src+", arp_tpa="+host_ip_dst+"  action=output:"+str(next_port)+ "\"")
			if graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is not None and graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is True:
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +graph_switch.name + " \"table=1,arp, arp_spa="+host_ip_dst+", arp_tpa="+host_ip_src+"  action=output:"+str(current_port)+ "\"")

			previous_node = node



def table_7(graph):
	""" table 7, add 222 as metadata if destination is not protected
	"""
	for switch in graph.switches:
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " + switch.name + " \"table=7, priority=10, action=load:222->OXM_OF_METADATA,resubmit(,10)\"")

def is_locked_destination_flip_daa(graph):
	""" table 7, add 11 as metadata if destination is protected
		used to dismiss announcemen bit
	"""
	for locked_host in graph.locked_hosts:
		locked_host_ip = graph.topo.nodeInfo(locked_host)["ip"].split("/")[0]
		for switch in graph.switches:
			# Is locked destination? TODO: Only install this on direct switches of locked hosts
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=7, ip,tcp, nw_dst="+locked_host_ip+" priority=50, action=move:NXM_OF_IP_SRC[]->NXM_NX_REG6[], move:NXM_OF_IP_DST[]->NXM_OF_IP_SRC[],move:NXM_NX_REG6[]->NXM_OF_IP_DST[],move:NXM_OF_TCP_SRC[]->NXM_NX_REG6[0..15], move:NXM_OF_TCP_DST[]->NXM_OF_TCP_SRC[],move:NXM_NX_REG6[0..15]->NXM_OF_TCP_DST[],load:111->OXM_OF_METADATA, resubmit(,10)\"")
		


def is_already_tracked(graph):
	""" table 10, check if packet is already tracked
	"""
	for switch in graph.switches:
		# table 10
		# is already tracked?
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=10,dl_vlan=1, priority=50, actions=resubmit(,119),resubmit(,200),resubmit(,201)\"")
		# if not, resubmit to check if tracked here
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=10, priority=10, actions=resubmit(,20),resubmit(,21)\"")



def is_already_tracked_with_daa(graph):
	""" table 10, table 11 
		checks if packet is already tracked using select groups instead of announcement bit
		used to dismiss announcemen bit
	"""
	variables = graph.variables
	switch_index = graph.switch_index
	path_weights = graph.path_weights

	cumulative_variables = calculate_path_explicit_cumulatives(variables,switch_index,graph)
	generate_path_to_burden_map_per_node(variables, switch_index,graph)

	# assert single route for source destination
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		if len(end_to_end_path_list)!= 1:
			print "no single route for source destination"
			return


	path_index = 0
	cntr = 0
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		source = source_destination[0]
		destination = source_destination[1]
		path = end_to_end_path_list[0]

		cumulative = 0
		
		host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
		host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]

		
		# INSTALL DISMISS ANNOUNCEMENT BIT GROUPS

		# CURRENT GROUP
		# FORWARD Direction
		group_id = path_index + 50

		
		for node in path:
			if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
				if switch_index.get(node.name) is not None:
					switch = node
					# add group
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
					cumulative = cumulative_variables[switch_index.get(node.name)][path_index]
					cumulative_rounded = int(round(cumulative))
					[r1,r2] = transform_independent_events(cumulative_rounded,path_weights[path_index]-cumulative_rounded)
					print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1)+",resubmit\(,11\),bucket=bucket_id:10,weight:"+str(r2)+",resubmit\(,17\)")
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=10,ip,metadata=222, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")
					cntr = cntr +1

		# PREVIOUS GROUP
		# FORWARD Direction
		group_id = path_index + 75
		previous = [0,100]
		for node in path:
			if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
				if switch_index.get(node.name) is not None:
					switch = node
					# add group
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
					cumulative = cumulative_variables[switch_index.get(node.name)][path_index]
					cumulative_rounded = int(round(cumulative))
					# add corresponding cumulative weight in switch
					[r1,r2] = transform_independent_events(cumulative_rounded,path_weights[path_index]-cumulative_rounded)
					print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(previous[0])+",resubmit\(,18\),bucket=bucket_id:10,weight:"+str(previous[1])+",resubmit\(,17\)")
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=11,ip,metadata=222, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")
					cntr = cntr +1
					previous = [r1,r2]

		# CURRENT GROUP
		# Backward Direction meta 123
		group_id = path_index + 150

		for node in path:
			if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
				if switch_index.get(node.name) is not None:
					switch = node
					# add group
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
					cumulative = cumulative_variables[switch_index.get(node.name)][path_index]
					cumulative_rounded = int(round(cumulative))
					# add corresponding cumulative weight in switch
					[r1,r2] = transform_independent_events(cumulative_rounded,path_weights[path_index]-cumulative_rounded)
					print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1)+",resubmit\(,11\),bucket=bucket_id:10,weight:"+str(r2)+",resubmit\(,18\)")
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=10,ip,metadata=111, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")
					cntr = cntr +1

		# PREVIOUS GROUP
		# Baclward Direction meta 123
		group_id = path_index + 175
		previous = [0,100]
		for node in path:
			if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
				if switch_index.get(node.name) is not None:
					switch = node
					# add group
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
					cumulative = cumulative_variables[switch_index.get(node.name)][path_index]
					cumulative_rounded = int(round(cumulative))
					# add corresponding cumulative weight in switch
					[r1,r2] = transform_independent_events(cumulative_rounded,path_weights[path_index]-cumulative_rounded)
					print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(previous[0])+",resubmit\(,18\),bucket=bucket_id:10,weight:"+str(previous[1])+",resubmit\(,17\)")
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=11,ip,metadata=111, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")
					cntr = cntr +1
					previous = [r1,r2]

		path_index = path_index + 1



def is_already_tracked_with_daa_additional_ff(graph):
	""" table 10, table 11 
		checks if packet is already tracked using select groups instead of announcement bit
		used to dismiss announcemen bit
		adds additional groups for fast-failover paths
	"""
	variables = graph.variables
	switch_index = graph.switch_index
	path_weights = graph.path_weights

	cumulative_variables = calculate_path_explicit_cumulatives(variables,switch_index,graph)

	fast_failover_routing_dict = graph.ff_paths
	path_index = 0
	
	
	#### get convergence in Fast Failover ####
	for ff_node,ff_node_dict in fast_failover_routing_dict.iteritems():
		for source_destination, source_destination_dict in ff_node_dict.iteritems():
			if source_destination_dict.get("paths") is not None:
				for ff_path_str, ff_path_dict in source_destination_dict["paths"].iteritems():
					if ff_path_dict.get("convergence_node") is None:
						print "convergence_node is None: fast failover dict not updated!"
						continue

					convergence_node_name = ff_path_dict.get("convergence_node")

					ff_source_name = source_destination.split(",")[0]
					ff_destination_name = source_destination.split(",")[1]
					
					corresponding_original_path = None
					host_ip_src = None
					host_ip_dst = None
					##### get corresponding original path
					for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
						source = source_destination[0]
						destination = source_destination[1]

						host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
						host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]

						if ff_source_name == source.name and ff_destination_name == destination.name:
							corresponding_original_path = end_to_end_path_list[0]
							break
					if corresponding_original_path is None:
						print "corresponding_original_path not found for ff_path: " +  str(ff_path_str)
						continue

					corresponding_original_path_str = get_path_str(corresponding_original_path)

					ff_max_tracking_node = get_previous_node_in_path_by_node_name(ff_path_str,convergence_node_name,graph)
					corresponding_original_max_tracking_node = get_previous_node_in_path_by_node_name(corresponding_original_path_str,convergence_node_name,graph)
					if ff_max_tracking_node is None:
						print "ff_max_tracking_node is None"
						continue
					if corresponding_original_max_tracking_node is None:
						print "corresponding_original_max_tracking_node is None"
						continue

					original_path_index = get_path_index_from_path_string(corresponding_original_path_str,graph)
					
					#### get min to propagate
					cumulative_min = cumulative_variables[graph.switch_index.get(ff_node)][original_path_index]
					
					#### get max to set at ff_max_tracking_node
					cumulative_max = cumulative_variables[graph.switch_index.get(corresponding_original_max_tracking_node.name)][original_path_index]
					
					### set is tracked here accordingly
					ff_path = get_path_from_path_str(ff_path_str,graph)
					started = False
					using_cumulative = None
					for ff_node_in_path in ff_path:
						if started:
							if ff_node_in_path.name == ff_max_tracking_node.name:
								using_max_cumulative = cumulative_max
							else:
								using_max_cumulative = cumulative_min

							cumulative_using_max_rounded = int(round(using_max_cumulative))						
							[r1_max,r2_max] = transform_independent_events(cumulative_using_max_rounded,path_weights[original_path_index]-cumulative_using_max_rounded)
							
							cumulative_min_rounded = int(round(cumulative_min))						
							[r1_min,r2_min] = transform_independent_events(cumulative_min_rounded,path_weights[original_path_index]-cumulative_min_rounded)
							
							# INSTALL DISMISS ANNOUNCEMENT BIT GROUPS
							
							# CURRENT GROUP
							# FORWARD Direction
							group_id = original_path_index + 50
							switch = ff_node_in_path
							# add group
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1_max)+",resubmit\(,11\),bucket=bucket_id:10,weight:"+str(r2_max)+",resubmit\(,17\)")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=10,ip,metadata=222, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")



							# PREVIOUS GROUP
							# FORWARD Direction
							group_id = original_path_index + 75
							# add group
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1_min)+",resubmit\(,18\),bucket=bucket_id:10,weight:"+str(r2_min)+",resubmit\(,17\)")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=11,ip,metadata=222, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")




							# CURRENT GROUP
							# Backward Direction meta 123
							group_id = original_path_index + 150
							# add group
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1_max)+",resubmit\(,11\),bucket=bucket_id:10,weight:"+str(r2_max)+",resubmit\(,18\)")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=10,ip,metadata=111, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")




							# PREVIOUS GROUP
							# Baclward Direction meta 123
							group_id = original_path_index + 175
							# add group
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1_min)+",resubmit\(,18\),bucket=bucket_id:10,weight:"+str(r2_min)+",resubmit\(,17\)")
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=11,ip,metadata=111, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")

							# ADD TRACKING GROUP
							group_id = original_path_index + 10
							# add group
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
							# add corresponding cumulative weight in switch
							print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1_max)+",resubmit\(,91\),bucket=bucket_id:10,weight:"+str(r2_max)+",resubmit\(,92\)")
							# add table 90 match on path, submit to group
							print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=90,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")

						if ff_node_in_path.name == ff_node:
							started = True


						### finsh
						if ff_node_in_path.name == ff_max_tracking_node.name:
							break


def install_double_resubmitting_daa(graph):
	""" table 17, table 18 
		aggregates resubmitting to:
			resubmit(,20),resubmit(,21): for is_tracked here
			resubmit(,200),resubmit(,201): for forwarding
		fixes src & destination fields if flipped
	"""
	if graph.switch_index is None:
		print "switch_index is None. Populate first"
		return

	for switch in graph.switches:
		node = switch
		
		if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:

			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=17,priority=10,ip, actions=resubmit(,20),resubmit(,21)"+ "\"")
			## fix if flipped in table 7
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=17,ip,tcp,priority=50,metadata=111,actions=move:NXM_OF_IP_DST[]->NXM_NX_REG6[], move:NXM_OF_IP_SRC[]->NXM_OF_IP_DST[],move:NXM_NX_REG6[]->NXM_OF_IP_SRC[],move:NXM_OF_TCP_DST[]->NXM_NX_REG6[0..15], move:NXM_OF_TCP_SRC[]->NXM_OF_TCP_DST[],move:NXM_NX_REG6[0..15]->NXM_OF_TCP_SRC[],resubmit(,20),resubmit(,21)"+ "\"")

			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=18,priority=10,ip, actions=resubmit(,119),resubmit(,200),resubmit(,201)"+ "\"")
			## fix if flipped in table 7
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=18,ip,tcp, priority=50,metadata=111,actions=move:NXM_OF_IP_DST[]->NXM_NX_REG6[], move:NXM_OF_IP_SRC[]->NXM_OF_IP_DST[],move:NXM_NX_REG6[]->NXM_OF_IP_SRC[],move:NXM_OF_TCP_DST[]->NXM_NX_REG6[0..15], move:NXM_OF_TCP_SRC[]->NXM_OF_TCP_DST[],move:NXM_NX_REG6[0..15]->NXM_OF_TCP_SRC[],resubmit(,119),resubmit(,200),resubmit(,201)"+ "\"")





def is_tracked_here(graph):
	""" table 21
		checks if packet is already tracked using announcement bit
	"""
	for switch in graph.switches:
		
		# if marked as tracked here, resubmit to tracking table
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=21, priority=50, reg0=2, actions=resubmit(,110)\"")
		# if not, resubmit to check if we should track here
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=21, priority=10, actions=resubmit(,30)\"")

def is_tracked_here_daa(graph):
	""" table 21
		checks if packet is already tracked in dismiss announcement bit
	"""
	for switch in graph.switches:
		# if marked as tracked here, resubmit to tracking table
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=21, priority=50, reg0=2, actions=resubmit(,110)\"")
		# if going in the reverse direction but not tracked here, drop
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=21,metadata=111, priority=30, actions=drop\"")
		# if not, resubmit to check if we should track here
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=21, priority=10, actions=resubmit(,30)\"")

def is_connection_initiating(graph):
	""" table 30
		checks if packet is a connection initiating packet
	"""
	for locked_host in graph.locked_hosts:
		host_ip = graph.topo.nodeInfo(locked_host)["ip"].split("/")[0]
		for switch in graph.switches:
			# Can initiate connection with TCP SYN:2? Policy for 10.0.1.1
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=30,ip,tcp, tcp_flags=2,nw_src="+host_ip+" priority=50, action=resubmit(,50)\"")
			# Can initiate connection with UDP? Policy for 10.0.1.1
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=30,ip,udp, nw_src="+host_ip+" priority=30, action=resubmit(,50)\"")
		
	for switch in graph.switches:
		# resubmit to check if last switch to origin
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=30, priority=10, action=resubmit(,70)\"")


	

def is_locked_destination(graph):
	""" table 50
		checks if destination is protected. Drop if true
	"""
	for locked_host in graph.locked_hosts:
		locked_host_ip = graph.topo.nodeInfo(locked_host)["ip"].split("/")[0]
		for switch in graph.switches:
			# Is locked destination? TODO: Only install this on direct switches of locked hosts
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=50, ip,nw_dst="+locked_host_ip+" priority=50, action=drop\"")
		
	for switch in graph.switches:
		# destination not locked
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=50, priority=10, action=resubmit(,90)\"")

def is_last_switch(graph):
	""" table 70
		checks if packet is at6 last switch to destination without being tracked yet. Drop if true
		used with announcement bit
	"""
	locked_hosts = []
	for node in graph.nodes:
	  if node.name in graph.topo.hosts():
	  	if node.name in graph.locked_hosts:
			locked_hosts.append(node)

	for locked_host in locked_hosts:
		for link in locked_host.links:
			switch = link.next_node
			port = link.next_port
			locked_host_ip = graph.topo.nodeInfo(locked_host.name)["ip"].split("/")[0]
			# last switch to locked host on tcp
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=70, ip, tcp, nw_dst="+locked_host_ip+" priority=50, action=drop\"")
			# last switch to locked host on udp
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=70, ip, udp, nw_dst="+locked_host_ip+" priority=30, action=drop\"")
	
	for switch in graph.switches:
		# if not last switch to origin and ip (not last switch to origin or arp), resubmit to forward
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=70, priority=10, action=resubmit(,119),resubmit(,200),resubmit(,201)\"")





def not_tracking_at_all(graph):
	""" table 90
		packet matches on this flow if a switch is not participating in the tracking procedure.
		Resubmits packet to table 92. Assumes packet has been denied for tracking
	"""
	for switch in graph.switches:
		# is already tracked?
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=90,,priority=10, actions=resubmit(,92)\"")
		

def install_L3_learn_groups(graph):
	""" table 90
		project packet on select group to decide whether to track
		used in L3 routing
	"""

	variables = graph.variables
	switch_index = graph.switch_index
	path_weights = graph.path_weights

	graph.switch_index = switch_index
	cumulative_variables = calculate_path_explicit_cumulatives(variables,switch_index,graph)
	generate_path_to_burden_map_per_node(variables, switch_index,graph)

	# assert single route for source destination
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		if len(end_to_end_path_list)!= 1:
			print "no single route for source destination"
			return


	path_index = 0
	cntr = 0
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		source = source_destination[0]
		destination = source_destination[1]
		path = end_to_end_path_list[0]

		group_id = path_index + 10
		cumulative = 0
		
		host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
		host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]

		for node in path:
			if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
				if switch_index.get(node.name) is not None:
					switch = node
					# add group
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
					cumulative = cumulative_variables[switch_index.get(node.name)][path_index]
					cumulative_rounded = int(round(cumulative))
					# add corresponding cumulative weight in switch
					[r1,r2] = transform_independent_events(cumulative_rounded,path_weights[path_index]-cumulative_rounded)
					print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1)+",resubmit\(,91\),bucket=bucket_id:10,weight:"+str(r2)+",resubmit\(,92\)")
					
					# add table 90 match on path, submit to group
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=90,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")
					cntr = cntr +1

		path_index = path_index + 1



def install_L4_LB_additive_asserted_cumulatives_learn_groups(graph):
	""" table 90
		project packet on select group to decide whether to track
		used in L4-LB CAA
	"""

	variables = graph.variables
	switch_index = graph.switch_index
	path_weights = graph.path_weights

	generate_path_to_burden_map_per_node(variables, switch_index,graph)
	generate_cumulative_burden_values_in_map_per_node(variables, switch_index,graph,path_weights)
	generate_asserted_cumulatives(variables, switch_index,graph,path_weights)

	cntr = 0
	installed_learn_groups_dict = dict()
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		source = source_destination[0]
		destination = source_destination[1]
		taken_nodes = []
		for path in end_to_end_path_list:

			
			cumulative = 0
			
			host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
			host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]

			for node in path:


				if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
					if switch_index.get(node.name) is not None:
						switch = node

						if installed_learn_groups_dict.get(switch.name) is None:
							installed_learn_groups_dict[switch.name] = dict()
							installed_learn_groups_dict[switch.name]["group_id"] = 10
						if installed_learn_groups_dict[switch.name].get((source.name,destination.name)) is None:
							installed_learn_groups_dict[switch.name][(source.name,destination.name)] = True
							pass
						else:
							continue

						asserted_additive_cumulative_percentage = switch.param_dict["asserted_cumulatives_params"][(source.name,destination.name)]["asserted_additive_cumulative_percentage"]
						cumulative = asserted_additive_cumulative_percentage
						
						group_id = installed_learn_groups_dict[switch.name]["group_id"]
						installed_learn_groups_dict[switch.name]["group_id"] = installed_learn_groups_dict[switch.name]["group_id"] + 1
						
						# add group
						print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch.name + " group_id="+ str(group_id) + ",type=all")
						cumulative_rounded = int(round(cumulative))
						# add corresponding cumulative weight in switch
						a1 = int(round(cumulative*1000))
						b1 = 1000-a1
						[r1,r2] = transform_independent_events(a1,b1)
						print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1)+",resubmit\(,91\),bucket=bucket_id:10,weight:"+str(r2)+",resubmit\(,92\)")
						
						print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=90,ip,nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")
						cntr = cntr +1


def install_cumulative_aggregate_learn_groups(graph):
	""" table 90
		project packet on select group to decide whether to track
		used in L4_LB PAA
	"""

	variables = graph.variables
	switch_index = graph.switch_index
	path_weights = graph.path_weights

	generate_path_to_burden_map_per_node(variables, switch_index,graph)
	generate_cumulative_burden_values_in_map_per_node(variables, switch_index,graph,path_weights)
	generate_cumulative_aggregate_weights(variables, switch_index,graph,path_weights)


	cntr = 0
	

	for node in graph.nodes:
 		if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
 			graph_switch = node
 			if graph_switch.param_dict.get("path_to_burden_map") is not None:

 				group_id_incr = 0
 				for source_destination in graph_switch.param_dict["cumulative_aggregate_weight_map"]:
 					source = source_destination[0]
					destination = source_destination[1]
 					host_ip_src = graph.topo.nodeInfo(source)["ip"].split("/")[0]
					host_ip_dst = graph.topo.nodeInfo(destination)["ip"].split("/")[0]



 					cum_aggregate = graph_switch.param_dict["cumulative_aggregate_weight_map"][(source,destination)]["cumulative_aggregate_weight"]
					aggregate_source_destination_traffic_weight = graph_switch.param_dict["cumulative_aggregate_weight_map"][(source,destination)]["cumulative_aggregate_sum_path_weight"]
					


					
					group_id = group_id_incr + 10
					cum_aggregate_int = int(round(cum_aggregate))
					[r1,r2] = transform_independent_events(cum_aggregate_int,aggregate_source_destination_traffic_weight-cum_aggregate_int)

					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + graph_switch.name + " group_id="+ str(group_id) + ",type=all")
					
					print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + graph_switch.name + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),bucket=bucket_id:11,weight:"+str(r1)+",resubmit\(,91\),bucket=bucket_id:10,weight:"+str(r2)+",resubmit\(,92\)")
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +graph_switch.name + " \"table=90,ip,nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")
 					group_id_incr = group_id_incr + 1




def accept_tracking(graph):
	""" table 91
		if tracking was accepted in table 90, a new flow is learnt at table 20
	"""
	for switch in graph.switches:
		# table 91
		# if decision was made to track here, learn new tracking flow for tcp
		# TODO: initiator learnt flow must have its timeout alone since it doesnt receive a fin
		# if decision was made to track here, learn new tracking flow for tcp
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=91, priority=50, ip ,tcp, actions=learn(table=20,fin_hard_timeout=200,eth_type=0x800,NXM_OF_IP_PROTO(6),NXM_OF_IP_SRC[]=NXM_OF_IP_SRC[],NXM_OF_IP_DST[]=NXM_OF_IP_DST[],NXM_OF_TCP_SRC[]=NXM_OF_TCP_SRC[],NXM_OF_TCP_DST[]=NXM_OF_TCP_DST[],priority=50,load:2->NXM_NX_REG0[0..15]),learn(table=20,fin_hard_timeout=200,eth_type=0x800,NXM_OF_IP_PROTO(6), NXM_OF_IP_DST[]=NXM_OF_IP_SRC[], NXM_OF_IP_SRC[]=NXM_OF_IP_DST[],NXM_OF_TCP_SRC[]=NXM_OF_TCP_DST[],NXM_OF_TCP_DST[]=NXM_OF_TCP_SRC[],priority=50,load:2->NXM_NX_REG0[0..15]),resubmit(,110)\"")
		# if decision was made to track here, learn new tracking flow for udp
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=91, priority=50, ip ,udp, actions=learn(table=20, hard_timeout=" + HARD_TIMEOUT + ", eth_type=0x800, NXM_OF_IP_PROTO(11),  NXM_OF_IP_SRC[]=NXM_OF_IP_SRC[],NXM_OF_IP_DST[]=NXM_OF_IP_DST[], priority=50, load:2->NXM_NX_REG0[0..15]),learn(table=20, hard_timeout=" + HARD_TIMEOUT + ", eth_type=0x800,NXM_OF_IP_PROTO(11),  NXM_OF_IP_DST[]=NXM_OF_IP_SRC[], NXM_OF_IP_SRC[]=NXM_OF_IP_DST[], priority=50, load:2->NXM_NX_REG0[0..15]),resubmit(,110)\"")
		

def tracking_denied_forward(graph):
	""" table 92
		if tracking was denied, forward packet
	"""
	for switch in graph.switches:
		# table 92
		# if decision was made not to track here, resubmit to forwarding (TODO: there should not be a vlan tag, so why check?)
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=92,priority=30, action=resubmit(,119),resubmit(,200),resubmit(,201)\"")




def tracking_table(graph):
	""" table 110
		perform tracking of connection states here.
		push VLAN if using announcement bit
	"""
	for switch in graph.switches:
		# table 110
		# perform tracking, push vlan, and resubmit to forward
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=110, priority=10,action=push_vlan:0x8100,mod_vlan_vid:1,resubmit(,119),resubmit(,200),resubmit(,201)\"")

def tracking_table_daa(graph):
	""" table 110
		perform tracking of connection states here.
		no VLAN pushed if dismissing announcement bit
	"""
	for switch in graph.switches:
		# table 110
		# perform tracking, push vlan, and resubmit to forward
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=110, priority=10,action=resubmit(,119),resubmit(,200),resubmit(,201)\"")


def pop_vlan_for_hosts(graph):
	""" table 200
		flags register if packet is vlan tagged at last switch to host. To be popped in table 201
	"""
	hosts = []
	for node in graph.nodes:
		if node.name in graph.topo.hosts():
			hosts.append(node)

	for host in hosts:
		host_ip = graph.topo.nodeInfo(host.name)["ip"].split("/")[0]
		for link in host.links:
			switch = link.next_node
			port = link.next_port
			# table 0
			# removed resubmit to table 2
			print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=200, priority=50,ip, nw_dst="+host_ip + ", actions=load:3->NXM_NX_REG2[0..15]\"")



def pop_vlan(graph):
	""" table 201
		pops VLAN before forwarding to host
	"""
	for switch in graph.switches:
		# table 201
		# pop vlan if direct switch
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=201, priority=50,dl_vlan=1, reg2=3, action=strip_vlan,resubmit(,202)\"")
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=201, priority=30, action=resubmit(,202)\"")


def install_symmetric_backward_flows(graph):
	""" table 119, table 202
		reactively learns backward symmetric routes in the network
	"""
	for switch in graph.switches:
		# table 10
		# is already tracked?
		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=202,,priority=10, actions=resubmit(,203)\"")
		# if not, resubmit to check if tracked here		

		print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch.name + " \"table=119, priority=10,ip,tcp, actions=,learn(table=119,idle_timeout=50, eth_type=0x800,NXM_OF_IP_PROTO(6), NXM_OF_IP_DST[]=NXM_OF_IP_DST[], NXM_OF_IP_SRC[]=NXM_OF_IP_SRC[],NXM_OF_TCP_SRC[]=NXM_OF_TCP_SRC[],NXM_OF_TCP_DST[]=NXM_OF_TCP_DST[],priority=45,load:3->NXM_NX_REG6[0..15]),learn(table=203,idle_timeout=50, eth_type=0x800,NXM_OF_IP_PROTO(6), NXM_OF_IP_DST[]=NXM_OF_IP_SRC[], NXM_OF_IP_SRC[]=NXM_OF_IP_DST[],NXM_OF_TCP_SRC[]=NXM_OF_TCP_DST[],NXM_OF_TCP_DST[]=NXM_OF_TCP_SRC[],priority=45,output=in_port)\"")


def install_L3_routing_from_keep_paths(graph):
	""" table 202
		installs L3 routes in the network
	"""
	path_index = 0
	previous_node = None
	unique_end_to_end_path = None
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		
		source = source_destination[0]
		destination = source_destination[1]

		host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
		host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]



		if len(end_to_end_path_list)==1:
			unique_end_to_end_path = end_to_end_path_list[0]
		else:
			print "cannot install route from kept paths. No single route"
			continue

		for node in unique_end_to_end_path:
			graph_switch = node
			current_port = None
			next_port = None

			if graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is not None and graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is True:
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +graph_switch.name + " \"table=0,arp, actions=resubmit(,1)" + "\"")

			if previous_node is None:
				previous_node = node
				continue

			for link in graph_switch.links:
				if link.next_node is None:
					continue

				if link.next_node.name == previous_node.name:
					current_port = link.current_port
					next_port = link.next_port


			if graph.topo.nodeInfo(previous_node.name).get("isSwitch") is not None and graph.topo.nodeInfo(previous_node.name).get("isSwitch") is True:
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +previous_node.name + " \"table=202,priority=50 ,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=output:"+str(next_port)+ "\"")
			if graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is not None and graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is True:
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +graph_switch.name + " \"table=202,priority=50 ,ip, nw_src="+host_ip_dst+", nw_dst="+host_ip_src+"  action=output:"+str(current_port)+ "\"")

			previous_node = node


def install_L3_routing_from_keep_paths_with_FF(graph):
	""" table 202
		installs fast-failover L3 routes in the network
	"""

	ff_group_id = 200
	fast_failover_routing_dict = graph.ff_paths
	path_index = 0
	
	unique_end_to_end_path = None
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		
		source = source_destination[0]
		destination = source_destination[1]

		
		host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
		host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]

		### Fast Failover Paths ###
		fast_failover_detected_till_node = []

		if len(end_to_end_path_list)==1:
			unique_end_to_end_path = end_to_end_path_list[0]
		else:
			print "cannot install route from kept paths. No single route"
			continue

		#### get convergence in Fast Failover ####
		for ff_node,ff_node_dict in fast_failover_routing_dict.iteritems():
				if ff_node_dict.get(source.name + "," + destination.name) is not None:
					if ff_node_dict[source.name + "," + destination.name].get("paths") is not None:
						for ff_path_str,ff_path_dict in ff_node_dict[source.name + "," + destination.name]["paths"].iteritems():
							convergence_node = get_convergent_node_fast_failover_path(ff_path_str, get_path_str(end_to_end_path_list[0]),ff_node,graph)
							ff_path_dict["convergence_node"] = convergence_node
							if convergence_node is not None:
								ff_path = get_path_from_path_str(ff_path_str,graph)
								started = False
								finshed = False
								install_for_next_switch = False
								previous_node = None
								next_port = None
								for ff_node_in_path in ff_path:
									#### getting data
									if previous_node is not None:
										for link in ff_node_in_path.links:
											if link.next_node is None:
												continue

											if link.next_node.name == previous_node.name:
												current_port = link.current_port
												next_port = link.next_port

									if install_for_next_switch:
										if previous_node is not None:



											if graph.topo.nodeInfo(previous_node.name).get("isSwitch") is not None and graph.topo.nodeInfo(previous_node.name).get("isSwitch") is True:
												print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +previous_node.name + " \"table=202,priority=50 ,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=output:"+str(next_port)+ "\"")
										
										
									#### choose when to diverge
									if ff_node_in_path.name == convergence_node:
										finshed = True

									if started and not finshed:
										install_for_next_switch = True
									else:
										install_for_next_switch = False
									
									if ff_node_in_path.name == ff_node:
										started = True

									### get next port
									if previous_node is not None and previous_node.name == ff_node and started and ff_path_dict.get("next_port") is None and next_port is not None:
										ff_path_dict["next_port"] = next_port

									previous_node = ff_node_in_path

		previous_node = None
		for node in unique_end_to_end_path:


			graph_switch = node
			current_port = None
			next_port = None

			

			if graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is not None and graph.topo.nodeInfo(graph_switch.name).get("isSwitch") is True:
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +graph_switch.name + " \"table=0,arp, actions=resubmit(,1)" + "\"")

			if previous_node is None:
				previous_node = node
				continue

			for link in graph_switch.links:
				if link.next_node is None:
					continue

				if link.next_node.name == previous_node.name:
					current_port = link.current_port
					next_port = link.next_port

			# if FF, install FF group
			if fast_failover_routing_dict.get(previous_node.name) is not None and fast_failover_routing_dict.get(previous_node.name).get(source.name + "," + destination.name) is not None:
				ff_paths_dict = fast_failover_routing_dict.get(previous_node.name) is not None and fast_failover_routing_dict.get(previous_node.name).get(source.name + "," + destination.name).get("paths")
				ff_outport_list = []
				for ff_path, ff_path_dict in ff_paths_dict.iteritems():
					if ff_path_dict.get("next_port") is not None:
						ff_outport_list.append(ff_path_dict.get("next_port"))

				bucket_string = ""
				### add original port
				bucket_string = "bucket=watch_port:"+str(next_port)+",output:"+str(next_port)
				i = 0
				# build flow
				for ff_next_port in ff_outport_list:
					if len(ff_outport_list)>0:
						if i == 0:
							bucket_string = bucket_string + ","

						bucket_string += "bucket=watch_port:"+str(ff_next_port)+",output:"+str(ff_next_port)

						if i<len(ff_outport_list)-1:
							bucket_string = bucket_string + ","
						i = i + 1

				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + previous_node.name + " group_id="+ str(ff_group_id) + ",type=ff")
				print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + previous_node.name + " group_id="+ str(ff_group_id) + ",type=ff,"+bucket_string)
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +previous_node.name + " \"table=202,priority=50 ,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+str(ff_group_id)+ "\"")
				ff_group_id = ff_group_id + 1

			# Else, normal ROuting
			else:
				if graph.topo.nodeInfo(previous_node.name).get("isSwitch") is not None and graph.topo.nodeInfo(previous_node.name).get("isSwitch") is True:
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +previous_node.name + " \"table=202,priority=50 ,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=output:"+str(next_port)+ "\"")
				
			previous_node = node

def install_L4_symmetric_LB_routes(graph):
	""" table 202
		installs L4 routes at load-balancing switches
	"""

	path_explicit_LB_routes = dict()
	path_index = 0
	previous_node = None
	unique_end_to_end_path = None
	source_destination_group_id_incr = 0
	for source_destination,end_to_end_path_list in graph.network_general_path_list.iteritems():
		source_destination_group_id_incr = source_destination_group_id_incr + 1

		source = source_destination[0]
		destination = source_destination[1]	

		host_ip_src = graph.topo.nodeInfo(source.name)["ip"].split("/")[0]
		host_ip_dst = graph.topo.nodeInfo(destination.name)["ip"].split("/")[0]

		load_balancing_switches = dict()
		for path in end_to_end_path_list:
			for node in path:
				if graph.topo.nodeInfo(node.name).get("isSwitch") is not None and graph.topo.nodeInfo(node.name).get("isSwitch") is True:
					if load_balancing_switches.get(node.name) is None:
						load_balancing_switches[node.name] = dict()

					next_node = get_next_node_in_path(get_path_str(path),node,graph)
					if load_balancing_switches[node.name].get(next_node.name) is None:
						load_balancing_switches[node.name][next_node.name] = dict()
					if next_node is not None:
						link = get_link_from_to(node,next_node)
						if link is not None:
							load_balancing_switches[node.name][next_node.name]["link"] = link
							if load_balancing_switches[node.name][next_node.name].get("list_of_paths") is None:
								load_balancing_switches[node.name][next_node.name]["list_of_paths"] = []
							load_balancing_switches[node.name][next_node.name]["list_of_paths"].append(get_path_str(path))


		for switch,next_switches in load_balancing_switches.iteritems():
			if len(next_switches)>1:
				bucket_string = ""
				bucket_id = 1
				i = 0
				for next_switch,next_switch_dict in next_switches.iteritems():
					group_id = source_destination_group_id_incr + 100
					# TODO: fix path weights
					weight = len(next_switch_dict["list_of_paths"])*1000
					bucket_string = bucket_string + "bucket=bucket_id:"+str(bucket_id)+",weight:"+str(weight)+",output="+str(next_switch_dict["link"].current_port)
					if i<len(next_switches)-1:
						bucket_string = bucket_string + ","
					next_switch_dict["bucket_id"] = bucket_id
					bucket_id = bucket_id + 1
					i = i + 1
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-group " + switch + " group_id="+ str(group_id) + ",type=all")
				print commands.getoutput("ovs-ofctl -O OpenFlow15 mod-group " + switch + " group_id="+ str(group_id) + ",type=select,selection_method=hash,fields\(tcp_src,tcp_dst\),"+bucket_string)
				print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch + " \"table=202,priority=50 ,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=group:"+ str(group_id) + "\"")

			elif len(next_switches) == 1:
				for next_switch,next_switch_dict  in next_switches.iteritems():
					print commands.getoutput("ovs-ofctl -O OpenFlow15 add-flow " +switch + " \"table=202,priority=50 ,ip, nw_src="+host_ip_src+", nw_dst="+host_ip_dst+"  action=output:"+str(next_switch_dict["link"].current_port)+ "\"")

		path_explicit_LB_routes[(source.name,destination.name)] = load_balancing_switches































































