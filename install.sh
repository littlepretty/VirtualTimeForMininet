#!/bin/bash

# install dependencies
sudo apt-get update
sudo apt-get install autoconf automake libtool make gcc git \
socat psmisc xterm ssh iperf iproute telnet \
python-setuptools cgroup-bin ethtool help2man pyflakes pylint pep8 \
git-core autotools-dev pkg-config libc6-dev \

# clone OpenFlow and VTMininet's code
git clone git://openflowswitch.org/openflow.git openflow
git clone https://littlepretty@bitbucket.org/littlepretty/virtualtimeyjq.git vt_mininet

# clone Linux kernel's code
wget https://www.kernel.org/pub/linux/kernel/v3.x/linux-3.16.3.tar.gz
tar -zxvf linux-3.16.3.tar.gz
rm linux-3.16.3.tar.gz

# install Open vSwitch
sudo apt-get install openvswitch-datapath-dkms
sudo apt-get install openvswitch-switch
sudo apt-get install openvswitch-controller
sudo service openvswitch-controller stop
if [ -e /etc/init.d/openvswitch-controller ]; then
	sudo update-rc.d openvswitch-controller disable
fi

# install OpenFlow
pushd .
cd openflow
sudo ./boot.sh
sudo ./configure
patch -p1 < ../vt_mininet/mininet/util/openflow-patches/controller.patch
sudo make
sudo make install
popd

# patch kernel
pushd .
cd vt_mininet
git checkout low_level_time
cd kernel_changes
./transfer.sh ../../linux-3.16.3
popd

# build kernel
pushd .
cd linux-3.16.3
cp -vi /boot/config-`uname -r` .config
yes "" | make oldconfig
sudo ./build_all.sh
popd

# install VT-Mininet
pushd .
cd vt_mininet/mininet
sudo make clean
sudo make install
popd
