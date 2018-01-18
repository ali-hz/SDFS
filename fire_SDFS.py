import xmltodict
import pprint
pp = pprint.PrettyPrinter(indent=4)
import sys
import commands
current_path = commands.getoutput("pwd")
sys.path.insert(0, current_path + '/topologies')
sys.path.insert(0, current_path + '/SDFS-core')

# import SDFS core
from flows import *
from graph import *
# import topology files
from Elongated import *
from Elongated_2 import *
from Fourtire_2 import *
from Fourtire_4 import *
from Fourtire_6 import *
from Fourtire_8 import *
from Fourtire_10 import *



def install_flows(config_file):
	config = None

	# parse config file
	with open(config_file) as fd:
		config = xmltodict.parse(fd.read())


	if config is None:
		print "config file could not be parsed"
		return

	start = time.time()

	HARD_TIMEOUT="50"

	if config.get("config") is None:
		print "Error: Config file is missing config tag"
		return
	if config["config"].get("topo-name") is None:
		print "Error: Config file is missing topo-name value"
		return

	topo_class_name = config["config"]["topo-name"]

	routing = "L3"
	if config["config"].get("routing") is not None:
		routing = config["config"]["routing"]

	path_aggregariton = ""
	if routing == "L4":
		if config["config"].get("path-aggregariton") is None:
			print "Error: path-aggregation is not set for L4 routing"
			return
		else:
			path_aggregariton = config["config"]["path-aggregariton"]
	
	use_announcement_bit = True
	if config["config"].get("use-announcement-bit") is not None:
		if config["config"]["use-announcement-bit"].lower() == "false":
			use_announcement_bit =False

	use_fast_failover = False
	if config["config"].get("use-fast-failover") is not None:
		if config["config"]["use-fast-failover"].lower() == "true":
			use_fast_failover = True



	# create topo class instance
	topo = eval(topo_class_name)()

	if topo.routes is None:
		print "Error: Topology class: " + topo_class_name + " must have defined routes"
		return

	if topo.protected_hosts is None or topo.protected_hosts == []:
		print "Error: Topology class: " + topo_class_name + " must have defined protected_hosts"
		return


	# populate graph
	graph = Graph()
	is_graph_populated = graph.populate(topo,routing)
	

	# install flows
	if is_graph_populated:

		delete_all_flows(graph)
		delete_all_groups(graph)
		table_0(graph)
		table_7(graph)
		install_default_arp_forwarding(graph)
		pop_vlan_for_hosts(graph)
		is_connection_initiating(graph)
		is_locked_destination(graph)
		accept_tracking(graph)
		tracking_denied_forward(graph)
		pop_vlan(graph)
		not_tracking_at_all(graph)
		install_symmetric_backward_flows(graph)
		is_last_switch(graph)


		if use_announcement_bit:
			# UAA
			is_already_tracked(graph)
			is_tracked_here(graph)
			tracking_table(graph)
			

		else:
			# DAA
			is_already_tracked_with_daa(graph)
			is_tracked_here_daa(graph)
			tracking_table_daa(graph)
			





		if routing == "L3":
			install_L3_learn_groups(graph)
			if not use_fast_failover:
				install_L3_routing_from_keep_paths(graph)
			else:
				install_L3_routing_from_keep_paths_with_FF(graph)
		elif routing == "L4":
			install_L4_symmetric_LB_routes(graph)
			if path_aggregariton == "PAA":
				install_cumulative_aggregate_learn_groups(graph)
			elif path_aggregariton == "LWPA":
				install_L4_LB_longest_path_learn_groups(graph)
			elif path_aggregariton == "AAC":
				install_L4_LB_additive_asserted_cumulatives_learn_groups(graph)
			


		if not use_announcement_bit:
			# daa
			is_locked_destination_flip_daa(graph)
			if not use_fast_failover:
				pass
			else:
				is_already_tracked_with_daa_additional_ff(graph)
			
			install_double_resubmitting_daa(graph)


if __name__ == '__main__':
	install_flows('config.xml')





