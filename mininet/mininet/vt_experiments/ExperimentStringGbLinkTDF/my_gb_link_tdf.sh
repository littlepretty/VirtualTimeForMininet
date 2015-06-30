#!/bin/bash

# This script test whether we can initialize Mininet with
# a global TDF; if so, long chain topo can achieve ideal bandwidth

startPOX() {
    pushd `pwd`
    cd ../../../../pox
    ./pox.py log.level --DEBUG forwarding.l2_learning &
    popd
}

stopPOX() {
    killall controllers
}

testControllerBandwidth() {

    CONTROLLER=$1
    BW=$2
    TOPO=$3
    TDF=$4
    CPU=$5

	if [ "$1" == "NO" ]; then
		echo "****** KILLing or turn OFF POX controllers    ******"
		echo "****** Otherwise Mininet will try connect them******"
		stopPOX
	elif [ "$1" == "POX" ]; then
		echo "****** Please turn ON POX at another terminal ******"
		echo "****** Otherwise Mininet will blocking wait...******"
		startPOX
    fi

    LOG="Perf${TOPO}BW${BW}MTDF${TDF}"

	echo Test ${TOPO}$ topo with ${BW}Mbps link, ${CONTROLLER} controller, TDF as ${TDF}
	python mystringbw.py $LOG $CONTROLLER $BW $TDF $CPU

    stopPOX

    # equivalent to cleanup() in python API
    mn -c
}

usage() {
    echo $1 [Controller: NO or POX] [Bandwidth in Mbps] [TDF]
    exit 0
}

while getopts 'h' OPTION
do
    case $OPTION in
        h)  usage ControllerBandwidth;;
    esac
done

# vary TDF and BW 
TDFs="1 4"
# TDFs="1 4"
BWs="1000 2000"

for i in $TDFs; do
    for bw in $BWs; do
        echo "Test with TDF ${i}"
        testControllerBandwidth NO $bw String $i 0.5
    done 
done


