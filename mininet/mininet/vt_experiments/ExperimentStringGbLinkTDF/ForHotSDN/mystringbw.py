#!/usr/bin/python

"""
Test bandwidth (using iperf) on string/chain networks of varying size,
using both kernel and user datapaths.

We construct a network of 2 hosts and N switches, connected as follows:

       h1 - s1 - s2 - ... - sN - h2


WARNING: by default, the reference controller only supports 16
switches, so this test WILL NOT WORK unless you have recompiled
your controller to support 100 switches (or more.)

In addition to testing the bandwidth across varying numbers
of switches, this example demonstrates:

- creating a custom topology, StringTestTopo
- using the ping() and iperf() tests from Mininet()
- testing both the kernel and user switches

"""

from mininet.net import Mininet
from mininet.node import *
from mininet.topo import Topo
from mininet.log import lg
from mininet.util import irange, custom
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from functools import partial
from mininet.clean import cleanup
import sys
flush = sys.stdout.flush


class StringTestTopo( Topo ):
    "Topology for a string of N switches and 2 hosts."

    def __init__( self, N, **params ):

        # Initialize topology
        Topo.__init__( self, **params )

        # Create switches and hosts
        hosts = [ self.addHost( 'h%s' % h ) for h in irange( 1, 2 ) ]

        switches = [self.addSwitch( 's%s' % s ) for s in irange(1, N)]

        # Wire up hosts with switch
        self.addLink(hosts[0], switches[0])
        self.addLink(hosts[1], switches[ N - 1 ])

        last = None
        for switch in switches:
            if last:
                self.addLink(last, switch)
            last = switch

import numpy
import time
def stringBandwidthTest( lengths ):

    "Check bandwidth at various lengths along a switch chain."

    switchCount = lengths

    Topo = StringTestTopo( switchCount )

    net = Mininet( topo = Topo, host = host, switch = OVSKernelSwitch,
                  controller = controller, waitConnected = True,
                  link = link )
    # no tdf_adaptor to change TDF
    net.start()

    print "*** testing basic connectivity\n"
    src, dst = net.hosts
    if TDF == 1:
        num_rounds = 3
        for i in irange(1, num_rounds):
            ping_result = list(net.pingFull( [ src, dst ] ))
            # ping_result=[(host1), (host2)]
            # host = (src, dst, data)
            # data = (#sent, #received, rttmin, rttavg, rttmax, rttdev)
            print "Ping avg rtt = %s\n" % ping_result[0][2][3]
            rttavg = ping_result[0][2][3]
        dataFile.write( "RTT Avg = %s ms\n" % rttavg)

    print "*** testing bandwidth\n"
    iperf_time = 1
    bandwidth = net.iperf( [src, dst], l4Type = 'TCP', format = 'm', time=iperf_time)
    flush()
    iperf_time = 50
    #for i in irange(1, num_rounds):
    bandwidth = net.iperf( [src, dst], l4Type = 'TCP', format = 'm', time=iperf_time, interval=1, verbose=1, clifile=dataFile, serfile=dataFile )
    flush()

    net.stop()

if __name__ == '__main__':
    """
    To run this program with parameters, use:
    python mystringbw.py arg1 arg2 arg3 arg4
    arg1: log file name
    arg2: controller name or 'NO'
    arg3: tc bandwidth in mbps
    arg4: tdf as int
    arg5: cpu
    """
    lg.setLogLevel( 'info' )
    global TDF # for default mode

    arg_list = list(sys.argv)
    if len(arg_list) < 4:
        """default test parameters"""
        # file_name = "MininetTDF%s" % TDF
        file_name = "StringBWTestNoVirtualTime"
        controller = DefaultController
        link = partial( TCLink, bw = 100.0/float(TDF), delay='1ms' )
        set_cpu = 0.8
        TDF = 1
    else:
        file_name = arg_list[1]
        """in fact, Controller and Remotecontroller have no difference
        all we need to do is start or not start POX in another shell"""
        if arg_list[2] == "POX":
            controller = partial( RemoteController, ip = '127.0.0.1', port=6633 )
        else:
            controller = DefaultController
        TDF = float(arg_list[4])
        set_bw = float(arg_list[3])
        set_delay = "10us"
        set_cpu = float(arg_list[5])
        # link = partial( TCLink, bw = set_bw )
        link = partial( TCLink, bw = set_bw, delay=set_delay )

    """config host's cpu share and time dilation factor"""
    host = custom( CPULimitedHost, sched = 'cfs', period_us = 100000, cpu = set_cpu, tdf = TDF )

    """with w option, it automatically overwrite everytime"""
    dataFile = open('%s.log' % file_name, 'w')
    print "Results are written to %s.log file" % file_name
    dataFile.write("********* Running stringBandwidthTest *********\n")

    dataFile.flush()
    # seems mininet cannot handle more than 640 switches
    size = 30
    print "********* Running with %d switches, TDF = %d *********" % (size, TDF)
    stringBandwidthTest(size)

    cleanup()



