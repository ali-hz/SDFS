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




class Fourtire_8(Topo):

    protected_hosts = ["h1","h2","h3","h4","h5","h6","h7","h8"]

    routes = dict()
    routes["L3"] = dict()
    routes["L3"]["h1->s1->s5->s9->s11->h100"]= dict()
    routes["L3"]["h2->s2->s6->s9->s12->h101"] = dict()
    routes["L3"]["h3->s3->s7->s10->s11->h100"] = dict()
    routes["L3"]["h4->s4->s8->s10->s12->h101"] = dict()
    routes["L3"]["h5->s13->s15->s17->s18->h102"] = dict()
    routes["L3"]["h6->s14->s16->s17->s18->h102"] = dict()
    routes["L3"]["h7->s19->s21->s23->s24->h103"] = dict()
    routes["L3"]["h8->s20->s22->s23->s24->h103"] = dict()

    ff_paths = dict()
    ff_paths["s1"] = dict()
    ff_paths["s1"]["h1,h100"]= dict()
    ff_paths["s1"]["h1,h100"]["paths"] = dict()
    ff_paths["s1"]["h1,h100"]["paths"]["h1->s1->s6->s9->s11->h100"] = dict()

    routes["L4"] = dict()
    routes["L4"]["h1->s1->s5->s9->s11->h100"] = dict()
    routes["L4"]["h1->s1->s6->s9->s11->h100"] = dict()
    routes["L4"]["h2->s2->s6->s9->s12->h101"] = dict()
    routes["L4"]["h2->s2->s5->s9->s12->h101"] = dict()
    routes["L4"]["h3->s3->s7->s10->s11->h100"] = dict()
    routes["L4"]["h3->s3->s8->s10->s11->h100"] = dict()
    routes["L4"]["h4->s4->s8->s10->s12->h101"] = dict()
    routes["L4"]["h4->s4->s7->s10->s12->h101"] = dict()
    routes["L4"]["h5->s13->s15->s17->s18->h102"] = dict()
    routes["L4"]["h5->s13->s16->s17->s18->h102"] = dict()
    routes["L4"]["h6->s14->s16->s17->s18->h102"] = dict()
    routes["L4"]["h6->s14->s15->s17->s18->h102"] = dict()
    routes["L4"]["h7->s19->s21->s23->s24->h103"] = dict()
    routes["L4"]["h7->s19->s22->s23->s24->h103"] = dict()
    routes["L4"]["h8->s20->s22->s23->s24->h103"] = dict()
    routes["L4"]["h8->s20->s21->s23->s24->h103"] = dict()



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
        s13 = self.addSwitch('s13',protocols='OpenFlow15')
        s14 = self.addSwitch('s14',protocols='OpenFlow15')
        s15 = self.addSwitch('s15',protocols='OpenFlow15')
        s16 = self.addSwitch('s16',protocols='OpenFlow15')
        s17 = self.addSwitch('s17',protocols='OpenFlow15')
        s18 = self.addSwitch('s18',protocols='OpenFlow15')
        s19 = self.addSwitch('s19',protocols='OpenFlow15')
        s20 = self.addSwitch('s20',protocols='OpenFlow15')
        s21 = self.addSwitch('s21',protocols='OpenFlow15')
        s22 = self.addSwitch('s22',protocols='OpenFlow15')
        s23 = self.addSwitch('s23',protocols='OpenFlow15')
        s24 = self.addSwitch('s24',protocols='OpenFlow15')

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

        self.addLink(s13, s15)
        self.addLink(s13, s16)

        self.addLink(s14, s15)
        self.addLink(s14, s16)

        self.addLink(s15, s17)
        self.addLink(s16, s17)

        self.addLink(s17, s18)
        self.addLink(s17, s12)

        self.addLink(s10, s18)


        self.addLink(s19, s21)
        self.addLink(s19, s22)

        self.addLink(s20, s21)
        self.addLink(s20, s22)

        self.addLink(s21, s23)
        self.addLink(s22, s23)

        self.addLink(s23, s18)
        self.addLink(s23, s24)

        self.addLink(s17, s24)

        host1 = self.addHost('h1',
            ip="10.0.1.1/24")
        host2 = self.addHost('h2',
            ip="10.0.1.2/24")
        host3 = self.addHost('h3',
            ip="10.0.1.3/24")
        host4 = self.addHost('h4',
            ip="10.0.1.4/24")
        host5 = self.addHost('h5',
            ip="10.0.1.5/24")
        host6 = self.addHost('h6',
            ip="10.0.1.6/24")
        host7 = self.addHost('h7',
            ip="10.0.1.7/24")
        host8 = self.addHost('h8',
            ip="10.0.1.8/24")
        host100 = self.addHost('h100',
            ip="10.0.1.220/24")
        host101 = self.addHost('h101',
            ip="10.0.1.221/24")
        host102 = self.addHost('h102',
            ip="10.0.1.222/24")
        host103 = self.addHost('h103',
            ip="10.0.1.223/24")


        self.addLink(host1, 's1')
        self.addLink(host2, 's2')
        self.addLink(host3, 's3')
        self.addLink(host4, 's4')
        self.addLink(host5, 's13')
        self.addLink(host6, 's14')
        self.addLink(host7, 's19')
        self.addLink(host8, 's20')
        self.addLink(host100, 's11')
        self.addLink(host101, 's12')
        self.addLink(host102, 's18')
        self.addLink(host103, 's24')