from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.cli import CLI

net = Mininet(controller=None, switch=OVSSwitch)
s1 = net.addSwitch("s1", failMode="standalone")
h = {}
for name, ip in [("r1", "11"), ("r2", "12"), ("auth", "13"),
                 ("c1", "21"), ("c2", "22"), ("hc", "30")]:
    h[name] = net.addHost(name, ip=f"10.0.0.{ip}/24", mac=f"00:00:00:00:00:{ip}")
    net.addLink(h[name], s1)   # r1=port1, r2=port2, ... matches controller.py
net.start()

for c in ("c1", "c2"):
    h[c].cmd("arp -s 10.0.0.100 00:00:00:00:00:64")

h["auth"].cmd("python3 resolver.py --name auth --zone zone.json > auth.log 2>&1 &")
h["r1"].cmd("python3 resolver.py --name r1 --upstream 10.0.0.13 > r1.log 2>&1 &")
h["r2"].cmd("python3 resolver.py --name r2 --upstream 10.0.0.13 > r2.log 2>&1 &")
h["hc"].cmd("python3 controller.py > ctrl.log 2>&1 &")

CLI(net)
net.stop()
