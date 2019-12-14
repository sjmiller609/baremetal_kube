# Project Home Datacenter
### Low-effort Kubernetes on Bare Metal at home

I am building an automated Kubernetes cluster on bare metal in my basement. I hope this guide and the included automation can be useful for other tinkerers who may want to run a cluster in their home.

I am building this for myself, and I intend actually use it for real applications. For my use case, I am prioritizing ease of maintaince and repair. Life is easier when software can be fully reset or replaced instead of reconfigured when issues arise. That's why this automation is intended to deploy and keep up to date the entire configuration, as close to from-scratch as possible. I want it to be easy, given the hardware, to reproduce this system.

To achieve this goal, the following technologies are deployed, configured, or automated using Ansible:
- Host discovery ([dynamic inventory](https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html), [nmap](https://nmap.org/))
- Configure network and core services ([EdgeOS](https://www.ui.com/edgemax/edgerouter-lite/))
- Deploy and update operating systems on the nodes ([Container Linux, PXE network booting](https://coreos.com/os/docs/latest/booting-with-pxe.html))
- Deploy and update Kubernetes ([Kubespray](https://github.com/kubernetes-sigs/kubespray))
- Deploy and update applications ([Helm](https://github.com/helm/helm))

## Step 1: Site planning

I have a basement where my ISP's fiber optic hookup (ONT) is installed. There are plenty of outlets. I will worry about power draw after I run into the problem. After cleaning up the workspace, there is plenty of room to set up computers.

### Humidity and temperature

I figure it is warranted to consider these factors right off the bat, since I want to protect my investment.

I have a dehumidifer to keep the area in the right range. Basements are best kept between 30-50% humidity to keep the foundation healthy and to prevent mold. For the datacenter, lower humidities have a higher risk of electro static discharge - this could lead to fried circuts. Higher humidity carries the risk of condenstation. Online I have found the recommended range for a datacenter is 45-55% humidity, with 30% and 70% being critical. 45% is a good balance.

68-75 F is the ideal operating temperature. Luckily, this is also a comfortable living temperature, so I will let the furnace and AC take care of that.

### Dust

If you plan to keep your hardware in ship-shape, it's worth considering dust. Especially in a place like a basement, dust becomes a real problem. I cleaned my basement, but even still the dust seems likely to be a problem. To mitigate this issue, I have purchased non-woven polyster bags to put my computers in. [This study](https://nepis.epa.gov/Exe/ZyNET.exe/9101XVJT.txt?ZyActionD=ZyDocument&Client=EPA&Index=1976%20Thru%201980&Docs=&Query=&Time=&EndTime=&SearchMethod=1&TocRestrict=n&Toc=&TocEntry=&QField=&QFieldYear=&QFieldMonth=&QFieldDay=&UseQField=&IntQFieldOp=0&ExtQFieldOp=0&XmlQuery=&File=D%3A%5CZYFILES%5CINDEX%20DATA%5C76THRU80%5CTXT%5C00000035%5C9101XVJT.txt&User=ANONYMOUS&Password=anonymous&SortMethod=h%7C-&MaximumDocuments=1&FuzzyDegree=0&ImageQuality=r75g8/r75g8/x150y150g16/i425&Display=hpfr&DefSeekPage=x&SearchBack=ZyActionL&Back=ZyActionS&BackDesc=Results%20page&MaximumPages=1&ZyEntry=2#) may help inform your choice. I will find out along the way if these bags prove to protect from dust and not insulate the computers too much.

## Step 2: Plan architecture and buy hardware

The objective of this project is to set up a performant cluster that can actually be used for real-world applications. I want to be able to use normal containers, so I need to run on the right architecture. I want to run a variety of workloads, so I want there to be a fair amount of resources available initially, and the option to expand moving forward.

### Consider the applications

I may run a code repository server, a media server, a security system, home automation, or a web application backend. To highlight a real-world use case, I could serve a web application from a CDN, and run the database and any required controller logic in my datacenter. This is a cost-effective design. In 2019, CDNs are very affordable, but running Kuberentes clusters and managed database services are more costly. The nature of web apps usually demands very low latency for static content, but the services backend do not usually require such a low latency that it would not be acceptable to serve from a single geographic location. This is especially true when the applications will mostly be for personal or friend use.

### What are the requirements of the architecture?

Cost savings and flexibility:

I don't want to spend money on a rack-style setup because that will be too expensive. I also want to be able to mix and match different compute so I do not need to do costly fleet upgrades. I will prefer to use commodity, replacable hardware where I can.

Low maintainence overhead:

Ease of maintaince and repair are a high priority. Life is easier when software can be fully reset or replaced instead of reconfigured when issues arise. That's why this automation is intended to deploy and keep up to date the entire configuration, as close to from-scratch as possible. I want it to be easy, given the hardware, to reproduce this system.

Availability and fault tolerace:

Being hooked up to only one, non-business ISP means that I will not be able to achieve high availabilty. Should it ever get to the point that HA becomes necessary, then I may consider migrating the services to the cloud. I am mostly concerned that the architecture will allow the system to fix itself, but not that it will always be available.

### Compute:

- Master/Worker nodes: (1) Refurbished HP ProDesk business-class desktops (~$300 as of summer 2019).

This comes with a i5-4690 CPU @ 3.50GHz, 16GB memory, and a 500GB SSD. I can buy another one of these after I am running enough application to justify the cost. Having consulted the Kubespray documentation, I ought to be able to run the cluster with only one node at first.

- Laptop for the command center: HP EliteBook 8540w

This has a Intel(R) Core(TM) i7 CPU M 620 @ 2.67GHz and 8GB of RAM. This is where I will run and develop the automation. This is an old laptop that I have laying around. Pretty much any amd64 box will do. The only real hardware requirement are the correct architecture and a fast-enough NIC to serve OS images. I decided to have the command center separate from the cluster because it is annoying to experience interference with development and testing, so better to keep that isolated from the machines that will be more heavily automated.

### Network

We will need a managed router - a router that can be programatically configured (in this case, with Ansible).  For example, we will want to carefully control DHCP to configure PXE booting the Kubernetes nodes (see Step 3: Network), and we will want BGP features to enable bare metal load balancing in Kubernetes (TODO).

I chose the [EdgeRouter LITE](https://www.ui.com/edgemax/edgerouter-lite/) ($129) because it is an inexpensive and performant option. Ansible includes edgeos_* modules to configure routers running the EdgeOS operating system.

I also bought some CAT6 cabling ($29.99) and a generic, 8-port switch ($19.99).

### Storage

The worker node came with a 500GB SSD, which should be fine for now. Down the line, I hope to use local, SSD storage as ephemeral pod storage and provide persisent storage using NFS HDDs (TODO).

## Step 3: Network

I wrote an Ansible role to configure the router and core services. The role is specifically designed for the EdgeRouter LITE, but should work for any EdgeOS router.

There are three interfaces on the EdgeRouter LITE. They are configured like this:
- eth2: WAN, DHCP client, firewall
- eth0: LAN1, 192.168.1.0/24, DHCP server, DNS server + caching
- eth1: LAN2, 192.168.2.0/24, DNS server + caching

The eth2 port is connected with CAT6 cabling to the fiber optic (ONT) hookup. The eth0 port is connected to my WiFi router to serve my home network. The eth1 port is connected to the switch, and the switch it connected to the command center and the Kubernetes node(s).

Notes:
- DHCP is not running on the router for the datacenter subnet 192.168.2.0/24 because we will run a PXE and DHCP server for the datacenter from the command center.
- On initial set up, it is necessary to manually configure the interface of the command center (because there is no DHCP provider). For example:
```
# Check the name of your interface:
ifconfig
# Let's say your interface is named eth0:
# Set the IP address
sudo ifconfig eth0 192.168.1.100
# Set the netmask
sudo ifconfig eth0 netmask 255.255.255.0
# Check if we can reach the router
ssh ubnt@192.168.1.1
```
- After the router has been configured with Ansible, we will want to return our command center to using DHCP
```
# remove IP
sudo dhclient -r eth0
# check IP removed
ifconfig
# manually initiate DHCP
sudo dhclient -r eth0
```

## Step 4: Installing operating systems

I want to be able to easily add nodes to the cluster, and to have the operating system updated automatically. Container Linux is designed for this exact use case. Container Linux, when installed on a drive, will keep itself up to date automatically by downloading the new version to the drive, and booting from that on the next restart. Alternatively, the OS can be run on a node without any hard drive by booting the machine over the network. This is great because the process for adding a node to the network is just to change the boot order on the new device to network first, plugging it into the network, and turning it on.

An Ansible role pxe-server was developed to target the command center. It is expected for the command center to run any flavor of Ubuntu 18. I have developed it using Xubuntu 18.04. PXE booting is a protocol where the client (booting) machine will reach out over the network to grab a kernel and a configuration to launch itself.

Services deployed on the command center to enable network booting:
- DHCP server for the 192.168.2.0/24 subnet (configured to work with PXE)
- FTP server to serve the operating system ([Container Linux](https://stable.release.core-os.net/amd64-usr/current/))
- Apache 2 webserver to serve the installation configuration ([Container Linux config with is 'transpiled' into Ignition format](https://coreos.com/matchbox/docs/latest/container-linux-config.html))

## Step 5: Kubernetes

I chose [Kubespray](https://github.com/kubernetes-sigs/kubespray) to deploy Kubernetes because it is simple, customizable, and maintained. It seems to me the most stable and supported choice available as of 2019. During experimentation, I had success with deploying kuberentes on a single node, sharing the node as both a worker and the control plane.

As a part of host discovery, the Ansible dynamic inventory performs a network scan to detect nodes that have been booted into Container Linux. These nodes will be targeted for running both the Kubernetes control plane, and the worker nodes.

```
export KUBECONFIG=./inventory/artifacts/admin.conf
kubectl get nodes
NAME    STATUS   ROLES    AGE   VERSION
node0   Ready    master   51m   v1.16.2
```

```
$ kubectl get pods -n kube-system

NAME                                       READY   STATUS    RESTARTS   AGE
calico-kube-controllers-675cd8cb45-67zlv   1/1     Running   0          62m
calico-node-szmsz                          1/1     Running   1          62m
coredns-58687784f9-2hgq9                   0/1     Pending   0          13m
coredns-58687784f9-j6cjg                   1/1     Running   0          13m
dns-autoscaler-79599df498-77hkl            1/1     Running   0          61m
kube-apiserver-node0                       1/1     Running   0          62m
kube-controller-manager-node0              1/1     Running   0          62m
kube-proxy-tcccl                           1/1     Running   0          14m
kube-scheduler-node0                       1/1     Running   0          62m
kubernetes-dashboard-556b9ff8f8-k4pxq      1/1     Running   0          61m
nodelocaldns-fnn74                         1/1     Running   0          61m

$ kubectl describe pods -n kube-system coredns-58687784f9-2hgq9 | tail -n 1

  Warning  FailedScheduling  <unknown>  default-scheduler  0/1 nodes are available: 1 node(s) didn't match pod affinity/anti-affinity, 1 node(s) didn't satisfy existing pods anti-affinity rules.
```

That makes sense because there is only 1 node.

### experience with this plan

This when pretty well. I installed rook-ceph for persistent storage. In general, I have found Kubespray to be a bit slower to provision than I would hope. The focus is on safety and stability. It seems to me like all the extra time to install and configure each component (etcd, kube, CNI, storage, and so on..) could be avoided by making use of something that was already pre-baked. Kubespray was the first project for deploying kubernetes, and I think that the many options that have become built in are very useful.

I want to try out something that might enable a rapid test cycle for me. I am much more flexible on the kube environment than many Kubespray users might be, so I want to try something that will be faster and easier. Also, I want ARM support out of the box. There is a brand-new project called k3s by Rancher that is promising.

The thing I love about my current set up is that I can simply reboot all of my computers in order to start over with a fresh SSH-ready pool. This is enabled by Container Linux's very conveinient config. I tried to run k3s on container linux, but it seems there are a few bugs out of the box. The most tested target OS is Ubuntu. Since this is also the OS that I am most familiar with, I ought to refactor my PXE booting strategy to allow multiple distributions, including Ubuntu and CoreOS. It's too bad that Ubuntu preseed is not as nice as the container linux config, but let's give it a shot.

# PXE booting ubuntu

I already went through the process of setting up the DHCP, TFTP, and HTTP services required to get PXE booting working for container linux. I became aware of a few things about network booting in the process.
- BIOS is different than UEFI when it comes to net booting
- It's easier to coordinate the DHCP service into your PXE service if you can
- how to do DHCP config

## Let's choose a tool for PXE booting

So far, I was manually setting up the services required for net boot. I would like something easier. Ideally with the following features:
- manage DHCP conf to statically assign IPs
- find the right kernel, initrd for a distribution / target architecture (maybe automatically update them in the in the TFTP directory)
- handle both kinds of PXE booting and the weird edge cases

Initially, I was thinking Cobbler, but I ought to assess other options before starting.

### Matchbox

- Apache 2
- CoreOS project
- Go lang
- Coupled with CoreOS?
- Terraform provider!
- [Installation](https://coreos.com/matchbox/docs/latest/deployment.html) looks easy
- There is a nice diagram [here](https://coreos.com/matchbox/docs/latest/img/network-setup-flow.png) that I think is mostly applicable to generic PXE, not just matchbox. Helpful for conceptualizing what we need here.
- Limited documentation for anything besides the CoreOS path

### Foreman

- Integrated with configuration management
- Lots of requirements for the server
- Way more features than I intend to use

### MaaS

- Looks like it requires BMC / remote hardware management capabilities. This is in order to support cloud-like features of turning off the hardware, but my intention is to just reboot hosts in order to have them re-provisioned.

### FAI

- Getting started is advertising exactly what I want, and nothing else
- The most recent version was published a couple of months ago - sep '19

### Cobbler

I'm going to go with Cobbler for now since it seems like it's a bit more ironed out and is not biased or otherwise incentivized to support one particular OS.

One immediate downside is there is not a pacakge ready to go for Ubuntu 18.04.
