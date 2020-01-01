# Home Datacenter

Features:
- Provision a bare metal Kubernetes cluster automatically
- Automatically delete and re-provision the cluster, including re-installing the OS on all nodes
- Persistent storage external to Kubernetes
- Configure a network

## How does it work?

One server runs automation to reinstall nodes' operating systems and install Kubernetes. This server also provides persistent storage to Kubernetes such that deleting the cluster does not lose your data. The automation is designed to destroy the cluster and re-create it from scratch each time, ensuring it's easy to fix. This was set up with the Kubernetes developer or tinkerer in mind - ease of use and minimal complexity is preferred.

![In this demo, I redeploy kubernetes, then launch an app](images/home_datacenter.gif)

## Prerequisites

- One EdgeOS router
- Two or more AMD64 computers
- Enough cabling or additional networking equipment to connect all the computers (e.g. one ethernet switch, one cable to connect the switch to the router, and an additional cable for each computer)
- Know how to reconfigure boot order

## Setup:

### Step 0 - back up data

Back up all data you care about. This automation includes a feature to automatically and remotely reinstall operating systems. This should only happen to computers in the datacenter network that are booted from the network.

### Step 1 - download software

- [Install Ubuntu](https://tutorials.ubuntu.com/tutorial/tutorial-install-ubuntu-desktop#0) 18.04 on one of the computers
- Clone this repository
- Assume all following software steps use this environment

### Step 2 - put the hardware together

All the computers should be in the same Layer 2 network and that network should be plugged into the EdgeOS router on eth1. The EdgeOS router's eth2 port should be plugged into the internet (e.g. your modem). The eth0 port can be plugged into your home network router (wifi).

Example:

- Connect all computers to the same switch (ethernet), including the machine you installed Ubuntu on
- Connect the switch to the EdgeOS router on eth1
- Unplug your wifi router from your modem
- Connect the EdgeOS router's eth2 to your modem
- Connect the EdgeOS router's eth0 to your home wifi (optional to restore home network)
- For all computers other than the one you installed Ubuntu on, configure the network as first in the boot order

## Step 3 - deploy the datacenter

From the root of this repository, run this script
```
./init
```

## Next steps

### Data storage

Store your data at /data on the Ubuntu server, it is the only thing designed not to be erased when the script is re-run. You are still responsible for your own data.

### Reset Kubernetes

Just run the script again.

# Tools

The following tools are used:

- Host discovery ([dynamic inventory](https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html), [nmap](https://nmap.org/))
- Configure network ([EdgeOS](https://www.ui.com/edgemax/edgerouter-lite/))
- Deploy and update operating systems ([Container Linux, PXE network booting](https://coreos.com/os/docs/latest/booting-with-pxe.html))
- Kubernetes ([k3s](https://github.com/rancher/k3s))
- Kubernetes-external persistent storage (NFS using [geerlingguy's role](https://github.com/geerlingguy/ansible-role-nfs))

If you are looking for some applications to install, feel free to use [my applications](https://github.com/sjmiller609/my_apps.git)
