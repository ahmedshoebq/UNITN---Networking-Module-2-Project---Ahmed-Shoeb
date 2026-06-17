from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel
import time

class SimpleSDN(Topo):
    def build(self):
        # Hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Switches
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', protocols='OpenFlow13')

        # Links
        self.addLink(h1, s1)
        self.addLink(s1, s2)
        self.addLink(s2, h2)

def run():
    topo = SimpleSDN()

    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=True
    )

    # Add remote Ryu controller
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6633
    )

    net.start()

    # Force switches to use OpenFlow 1.3 and point to controller
    for sw in ['s1', 's2']:
        net.get(sw).cmd(f'ovs-vsctl set bridge {sw} protocols=OpenFlow13')
        net.get(sw).cmd(f'ovs-vsctl set-controller {sw} tcp:127.0.0.1:6633')

    # Give controller time to connect
print("\n*** Waiting for controller to connect...")
import time
for i in range(10):
    result = net.get('s1').cmd('ovs-vsctl get bridge s1 controller')
    if '6633' in result:
        print("*** Controller connected.")
        break
    time.sleep(1)

    print("\n*** Network started. Testing connectivity...\n")
    net.pingAll()

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
