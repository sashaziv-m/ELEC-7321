#!/bin/bash

ip netns add ns1  # create namespace
ip link add veth0 type veth peer name veth1 # create veth pair
ip link set veth1 netns ns1  # Move one end of veth to namespace

ip netns exec ns1 ip addr add 192.168.76.2/24 dev veth1
ip netns exec ns1 ip link set veth1 up

ip addr add 192.168.76.1/24 dev veth0
ip link set veth0 up
