from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
import csv, time, os

class CSVLogger(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(CSVLogger, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.filename = "traffic_data.csv"

        # Only write header if file does not already exist
        # Prevents data loss if Ryu restarts mid-session
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "datapath", "port",
                                 "rx_bytes", "tx_bytes"])

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        dp = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[dp.id] = dp
        elif ev.state == DEAD_DISPATCHER:
            if dp.id in self.datapaths:
                del self.datapaths[dp.id]

    def _monitor(self):
        while True:
            for dp in list(self.datapaths.values()):
                self._request_stats(dp)
            hub.sleep(5)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPPortStatsRequest(datapath, 0, datapath.ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        now = time.strftime("%H:%M:%S")
        ofproto = ev.msg.datapath.ofproto

        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            for stat in body:
                # Skip OFPP_LOCAL — internal management port, never real traffic
                if stat.port_no == ofproto.OFPP_LOCAL:
                    continue
                writer.writerow([now, ev.msg.datapath.id,
                                 stat.port_no, stat.rx_bytes, stat.tx_bytes])
                                 