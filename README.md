
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
