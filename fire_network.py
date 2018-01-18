import xmltodict
import pprint
pp = pprint.PrettyPrinter(indent=4)
import sys
import commands
current_path = commands.getoutput("pwd")
sys.path.insert(0, current_path + '/topologies')



# import topology files
from Elongated import *
from Elongated_2 import *
from Fourtire_2 import *
from Fourtire_4 import *
from Fourtire_6 import *
from Fourtire_8 import *
from Fourtire_10 import *

config = None

with open('config.xml') as fd:
	config = xmltodict.parse(fd.read())

	# pp.pprint(config)
	# print config["config"]["topo-name"]




if __name__ == '__main__':
	topo_class_name = config["config"]["topo-name"]
	topo = eval(topo_class_name)()
	net = Mininet(topo=topo,controller=None)

	# Run network
	net.start()
	CLI( net )
	net.stop()


