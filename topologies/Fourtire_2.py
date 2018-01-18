import commands
import random

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import setLogLevel
from functools import partial
from mininet.node import RemoteController
import multiprocessing
import time


class Fourtire_2(Topo):



    protected_hosts = ["h1","h2"]

    routes = dict()
    routes["L3"] = dict()
    routes["L3"]["h1->s1->s5->s9->s11->h100"]= dict()
    routes["L3"]["h2->s2->s6->s9->s12->h101"] = dict()

    routes["L4"] = dict()
    routes["L4"]["h1->s1->s5->s9->s11->h100"] = dict()
    routes["L4"]["h1->s1->s6->s9->s11->h100"] = dict()
    routes["L4"]["h2->s2->s6->s9->s12->h101"] = dict()
    routes["L4"]["h2->s2->s5->s9->s12->h101"] = dict()


    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        
        s1 = self.addSwitch('s1',protocols='OpenFlow15')
        s2 = self.addSwitch('s2',protocols='OpenFlow15')
        s5 = self.addSwitch('s5',protocols='OpenFlow15')
        s6 = self.addSwitch('s6',protocols='OpenFlow15')
       
        s9 = self.addSwitch('s9',protocols='OpenFlow15')
      
        s11 = self.addSwitch('s11',protocols='OpenFlow15')

        self.addLink(s1, s5)
        self.addLink(s1, s6)
        self.addLink(s2, s5)
        self.addLink(s2, s6)


        self.addLink(s5, s9)
        self.addLink(s6, s9)

        self.addLink(s9, s11)


        host1 = self.addHost('h1',
            ip="10.0.1.1/24")
        host2 = self.addHost('h2',
            ip="10.0.1.2/24")
        host100 = self.addHost('h100',
            ip="10.0.1.220/24")

        self.addLink(host1, 's1')
        self.addLink(host2, 's2')
        self.addLink(host100, 's11')