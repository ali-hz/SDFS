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




class Elongated_2(Topo):
    protected_hosts = ["h1"]

    routes = dict()
    routes["L3"] = dict()


    routes["L4"] = dict()
    routes["L4"]["h1->s1->s2->s3->s4->s6->s7->s8->s11->s12->h2"] = dict()
    routes["L4"]["h1->s1->s2->s3->s4->s6->s7->s9->s10->s11->s12->h2"] = dict()
    routes["L4"]["h1->s1->s5->s6->s7->s8->s11->s12->h2"] = dict()
    routes["L4"]["h1->s1->s5->s6->s7->s9->s10->s11->s12->h2"] = dict()



    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        
        s1 = self.addSwitch('s1',protocols='OpenFlow15')
        s2 = self.addSwitch('s2',protocols='OpenFlow15')
        s3 = self.addSwitch('s3',protocols='OpenFlow15')
        s4 = self.addSwitch('s4',protocols='OpenFlow15')
        s5 = self.addSwitch('s5',protocols='OpenFlow15')
        s6 = self.addSwitch('s6',protocols='OpenFlow15')
        s7 = self.addSwitch('s7',protocols='OpenFlow15')
        s8 = self.addSwitch('s8',protocols='OpenFlow15')
        s9 = self.addSwitch('s9',protocols='OpenFlow15')
        s10 = self.addSwitch('s10',protocols='OpenFlow15')
        s11 = self.addSwitch('s11',protocols='OpenFlow15')
        s12 = self.addSwitch('s12',protocols='OpenFlow15')

        self.addLink(s1, s2)
        self.addLink(s1, s5)

        self.addLink(s2, s3)
        self.addLink(s3, s4)

        self.addLink(s4, s6)
        self.addLink(s5, s6)

        self.addLink(s6, s7)

        self.addLink(s7, s8)
        self.addLink(s7, s9)

        self.addLink(s9, s10)

        self.addLink(s8, s11)
        self.addLink(s10, s11)

        self.addLink(s11, s12)    
        host1 = self.addHost('h1',
            ip="10.0.1.1/24")
        host2 = self.addHost('h2',
            ip="10.0.1.2/24")

        self.addLink(host1, 's1')
        self.addLink(host2, 's12')

