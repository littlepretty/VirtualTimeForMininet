#!/usr/bin/python

"""
Test bandwidth (using iperf) on string/chain networks of fixed size 40,
using both kernel and user datapaths.

We construct a network of 2 hosts and N switches, connected as follows:

       h1 - s1 - s2 - ... - sN - h2


WARNING: by default, the reference controller only supports 16
switches, so this test WILL NOT WORK unless you have recompiled
your controller to support 100 switches (or more.)

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
import numpy
import time

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


def stringBandwidthTest( lengths ):

    "Check bandwidth at various lengths along a switch chain."

    switchCount = lengths

    topo = StringTestTopo( switchCount )

    net = Mininet( topo = topo, host = host, switch = OVSKernelSwitch,
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
        data_file.write( "RTT Avg = %s ms\n" % rttavg)
    else:
        net.ping( [src, dst] )

    print "*** testing bandwidth\n"

    num_rounds = 10
    client_history = []
    time = 25
    omit = 5
    for i in irange(1, num_rounds):
        # bandwidth = net.iperf( [src, dst], l4Type = 'UDP', udpBw='%sM'%set_bw, format = 'm', time=20, clifile=dataFile, serfile=dataFile )
        bandwidth = net.iperf( [src, dst], l4Type = 'TCP', format = 'm', time=time, omit=omit, clifile=dataFile, serfile=dataFile )
        flush()
        serout = bandwidth[0]
        cliout = bandwidth[1]

        if len(serout) > 0 and len(cliout) > 0:
            serDataStr, unit = serout.split(" ")
            serData = float(serDataStr)

            cliDataStr, unit = cliout.split(" ")
            cliData = float(cliDataStr)
            client_history.append(cliData)
            data_file.write( "%s\t%f\t%f\t%s\t%s\n" % ( switchCount, src.tdf, net.cpu_usage, serData, cliData ) )

    client_mean = numpy.mean(client_history)
    client_stdev = numpy.std(client_history)
    data_file.write( "Avg Throughtput = %f\n" % client_mean )
    data_file.write( "STD Throughput = %f\n" % client_stdev )
    print "AVG = %f " % client_mean
    print "STD = %f " % client_stdev
    data_file.write('\n\n')

    net.stop()
    return client_mean, client_stdev

def main(file_name, controller, tdf, set_cpu, set_bw, set_delay = "10us", size = 40):
    lg.setLogLevel( 'info' )

    """in fact, Controller and Remotecontroller have no difference
    all we need to do is start or not start POX in another shell"""
    if controller == "POX":
        controller = partial( RemoteController, ip = '127.0.0.1', port=6633 )
    else:
        controller = DefaultController
    link = partial( TCLink, bw = set_bw, delay = set_delay )

    """config host's cpu share and time dilation factor"""
    host = custom( CPULimitedHost, sched = 'cfs', period_us = 100000, cpu = set_cpu, tdf = tdf )

    """with w option, it automatically overwrite everytime"""
    data_file = open('%s.log' % file_name, 'w')
    print "Results are written to %s.log file" % file_name
    data_file.write("********* Running stringBandwidthTest *********\n")
    data_file.flush()

    # seems mininet cannot handle more than 640 switches
    print "********* Running with %d switches, TDF = %d *********" % (size, tdf)
    client_mean, client_stdev = stringBandwidthTest(size)

    cleanup()

if __name__ == '__main__':
    TDFs = [1, 4]
    BWs = [4000, 8000, 10000]
    for tdf in TDFs:
        for bw in BWs:
            file_name = "PerfStringBW%dMTDF%d" %(bw, tdf)
            main(file_name, "NO", tdf, 0.5, bw)
