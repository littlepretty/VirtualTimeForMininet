#!/bin/bash

# install dependencies
install_dep()
{
    sudo apt-get update
    sudo apt-get install autoconf automake libtool make gcc git \
    socat psmisc xterm ssh iperf iproute telnet \
    python-setuptools cgroup-bin ethtool help2man pyflakes pylint pep8 \
    git-core autotools-dev pkg-config libc6-dev \
}

# install Open vSwitch
install_ovs()
{
    sudo apt-get install openvswitch-datapath-dkms
    sudo apt-get install openvswitch-switch
    sudo apt-get install openvswitch-controller
    sudo service openvswitch-controller stop
    if [ -e /etc/init.d/openvswitch-controller ]; then
        sudo update-rc.d openvswitch-controller disable
    fi
}
# install OpenFlow
install_of()
{
    # git clone git://openflowswitch.org/openflow.git openflow
    cd $HOME/openflow
    sudo ./boot.sh
    sudo ./configure
    patch -p1 < ../vt_mininet/mininet/util/openflow-patches/controller.patch
    sudo make
    sudo make install
}
# patch kernel
patch_kernel()
{
    cd $HOME
    # clone Linux kernel's code
    wget https://www.kernel.org/pub/linux/kernel/v3.x/linux-3.16.3.tar.gz
    tar -zxvf linux-3.16.3.tar.gz
    rm linux-3.16.3.tar.gz

    cd /HOME/vt_mininet
    git checkout low_level_time
    cd kernel_changes
    ./transfer.sh ../linux-3.16.3

    # build kernel
    cd $HOME/linux-3.16.3
    cp -vi /boot/config-`uname -r` .config
    yes "" | make oldconfig
    sudo ./build_all.sh
}

# install VT-Mininet
install_vt_mininet()
{
    # clone VTMininet's code
    # git clone https://littlepretty@bitbucket.org/littlepretty/virtualtimeyjq.git vt_mininet
    install_dep
    install_of
    install_ovs
    patch_kernel

    cd $HOME/vt_mininet/mininet
    sudo make clean
    sudo make install
}

while getopts "akfsd" option; do
    case $option in
    a) install_vt_mininet;;
    k) patch_kernel;;
    f) install_of;;
    s) install_ovs;;
    d) install_dep;;
    ?) echo "invalid argument";;
    esac
done
