# generate_traffic.py

from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import setLogLevel
import time

ROUNDS         = 3
PING_COUNT     = 5
IPERF_DURATION = 10

class SimpleSDN(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        self.addLink(h1, s1)
        self.addLink(s1, s2)
        self.addLink(s2, h2)

def run():
    topo = SimpleSDN()
    net  = Mininet(topo=topo, controller=None,
                   switch=OVSKernelSwitch,
                   link=TCLink, autoSetMacs=True)
    c0 = net.addController('c0',
           controller=RemoteController,
           ip='127.0.0.1', port=6633)
    net.start()

    h1 = net.get('h1')
    h2 = net.get('h2')

    print("\n*** Verifying connectivity...")
    net.pingAll()

    for round_num in range(1, ROUNDS + 1):
        print(f"\n=== Traffic Round {round_num}/{ROUNDS} ===")

        print(f"  [ICMP] h1 -> h2 ({PING_COUNT} pings)")
        result = h1.cmd(f'ping -c {PING_COUNT} {h2.IP()}')
        print(result)
        time.sleep(1)

        print(f"  [TCP]  iperf h1->h2 ({IPERF_DURATION}s)")
        h2.cmd('iperf -s &')
        time.sleep(1)
        result = h1.cmd(f'iperf -c {h2.IP()} -t {IPERF_DURATION}')
        print(result)
        h2.cmd('kill %iperf')
        time.sleep(1)

    print("\n*** Traffic generation completed!")
    print("    Run train_svm_model.py next.\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()