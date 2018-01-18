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







class Fourtire_4(Topo):


    protected_hosts = ["h1","h2","h3","h4"]

    routes = dict()
    routes["L3"] = dict()
    routes["L3"]["h1->s1->s5->s9->s11->h100"]= dict()
    routes["L3"]["h2->s2->s6->s9->s12->h101"] = dict()
    routes["L3"]["h3->s3->s7->s10->s11->h100"] = dict()
    routes["L3"]["h4->s4->s8->s10->s12->h101"] = dict()


    ff_paths = dict()
    ff_paths["s1"] = dict()
    ff_paths["s1"]["h1,h100"]= dict()
    ff_paths["s1"]["h1,h100"]["paths"] = dict()
    ff_paths["s1"]["h1,h100"]["paths"]["h1->s1->s6->s9->s11->h100"] = dict()


    routes["L4"] = dict()
    routes["L4"]["h1->s1->s5->s9->s11->h100"] = dict()
    # routes["L4"]["h1->s1->s5->s9->s11->h100"]["weight"] = 400
    routes["L4"]["h1->s1->s6->s9->s11->h100"] = dict()
    routes["L4"]["h2->s2->s6->s9->s12->h101"] = dict()
    routes["L4"]["h2->s2->s5->s9->s12->h101"] = dict()
    routes["L4"]["h3->s3->s7->s10->s11->h100"] = dict()
    routes["L4"]["h3->s3->s8->s10->s11->h100"] = dict()
    routes["L4"]["h4->s4->s8->s10->s12->h101"] = dict()
    routes["L4"]["h4->s4->s7->s10->s12->h101"] = dict()


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

        self.addLink(s1, s5)
        self.addLink(s1, s6)
        self.addLink(s2, s5)
        self.addLink(s2, s6)

        self.addLink(s3, s7)
        self.addLink(s3, s8)

        self.addLink(s4, s7)
        self.addLink(s4, s8)

        self.addLink(s5, s9)
        self.addLink(s6, s9)

        self.addLink(s7, s10)
        self.addLink(s8, s10)

        self.addLink(s9, s11)
        self.addLink(s9, s12)

        self.addLink(s10, s11)
        self.addLink(s10, s12)

        host1 = self.addHost('h1',
            ip="10.0.1.1/24")
        host2 = self.addHost('h2',
            ip="10.0.1.2/24")
        host3 = self.addHost('h3',
            ip="10.0.1.3/24")
        host4 = self.addHost('h4',
            ip="10.0.1.4/24")
        host100 = self.addHost('h100',
            ip="10.0.1.220/24")
        host101 = self.addHost('h101',
            ip="10.0.1.221/24")
        
        self.addLink(host1, 's1')
        self.addLink(host2, 's2')
        self.addLink(host3, 's3')
        self.addLink(host4, 's4')
        self.addLink(host100, 's11')
        self.addLink(host101, 's12')