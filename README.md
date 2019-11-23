
Configure an interface manually
```
sudo ifconfig eth0 192.168.1.100
sudo ifconfig eth0 netmask 255.255.255.0
```

Test DHCP
```
# remove IP
sudo dhclient -r eth0

# check IP removed
ifconfig

# manually do DHCP
sudo dhclient -r eth0
```

# Running Kubernetes on Bare Metal

There are a few how-tos online about running Kubernetes on a baremetal build at home. I have wondered, what does it take to build a production-grade cluster? I figured I would give it a shot in my basement, I call it 'project home datacenter'.

In the process of this project, I have found it's necessary to dig into the nitty-gritty time and time again. Since cloud providers are so prevalent these days, it's easy for younger technologists like myselft to take for granted everything that goes into making it happen. It certainly is a breeze these days to serve your website to the whole world! CDNs like CloudFront and Netifly make it so easy. For 'project home datacenter', I haved needed to consider temperature, humidity, dust, networking protocols, PXE booting, and much more. This is not a project for the faint of heart, and it's really only interesting to those who are motivated by the pursuit itself. I like tinkering, so I have had a blast. If there are those out there who dream of running it all at home, using the latest, and sexiest techologies (even when not really necessary) read on...

## Step 1: site planning and preparation

I used to work in a datacenter at Cisco. I thought it was interesting to learn that one of the most expensive parts of the datacenter build is floor space - that is, the room that the equipment takes up in the build is a significant portion of the cost, even compared to the hardware itself. As a recently new homeowner, I have certainly found this to be the case. Luckily, I have a nice location in my basement to set up my new datacenter. The only problem is that it seems like nobody has come down here in 25 years.

Mold remediation:

First, I remeditated the mold issue. My uncle in law has a nice recipe for those who are interested - 30% bleach and 70% water to fill up two gallons, then add two cups of trisodium phosphate. This is a very abrasive and highly oxidizing mixture, so gloves are recommended. Pour this mixture in a spray container, like you would use for spraying weeds, and spray it on all the effected areas. I found that my eyes were stinging, so I figure that means it's doing a good job to kill the mold. After a few hours, do it again. Wait a day or two for the area to be less painful to be in. It should be pretty easy now with a steel brush to scrape the mold off of the walls. Sweep the floor, and



I have traditional IT experience from school and work, but now I'm being faced with a new challenge - Kubernetes.
