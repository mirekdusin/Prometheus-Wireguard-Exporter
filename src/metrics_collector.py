import subprocess
import time

from prometheus_client import Gauge
from fastapi.exceptions import HTTPException
from logger import *
from settings import *


class MetricsCollector:
    def __init__(self, wg_path):
        self.wg_path = self.check_wg_path(wg_path)

        self.labels = ['interface', 'public_key', 'endpoint', 'allowed_ips', 'name']
        self.handshake_gauge = Gauge('wireguard_latest_handshake_timestamp',
                                     'Wireguard latest handshake timestamp',
                                     self.labels)
        self.received_gauge = Gauge('wireguard_bits_received',
                                    'Wireguard bits received',
                                    self.labels)
        self.sent_gauge = Gauge('wireguard_bits_sent',
                                'Wireguard bits sent',
                                self.labels)
        self.active_gauge = Gauge('wireguard_peer_active',
                                  'Whether the Wireguard peer was active in the last 2 minutes',
                                  self.labels)

        self.last_labels = {}
        self.names = {}

    @staticmethod
    def check_wg_path(wg_path):
        if not os.path.exists(wg_path):
            logger.exception(f'File {wg_path} does not exist')
            raise HTTPException(status_code=500, detail=f'File {wg_path} does not exist')
        return wg_path

    def collect_metrics(self):
        output = self.execute_wg_command()
        peers = self.extract_metrics_from_wg_output(output)
        self.set_gauge_values(peers)

    def execute_wg_command(self):
        try:
            output = subprocess.check_output([self.wg_path, 'show', 'all', 'dump']).decode().strip()
        except subprocess.CalledProcessError as e:
            logger.exception(f'Failed to get Wireguard metrics: {e}')
            raise HTTPException(status_code=500, detail=f'Failed to get Wireguard metrics: {e}')
        return output

    def extract_metrics_from_wg_output(self, output):
       peers = {
           fields[1]: {
               'interface': fields[0],
               'public_key': fields[1],
               'name': self.find_config_file(fields[1]),
               'endpoint': fields[3].split(':')[0] if fields[3] != '(none)' else '',
               'allowed_ips': fields[4],
               'active': 1 if len(fields) > 5 and (time.time() - int(fields[5])) <= 125 else 0,
               'last_handshake': int(fields[5]) if len(fields) > 5 else 0,
               'received': int(fields[6]) if len(fields) > 6 else 0,
               'sent': int(fields[7]) if len(fields) > 7 else 0
           } for fields in (line.split('\t') for line in output.split('\n')[1:])
       }
       return list(peers.values())

    def set_gauge_values(self, peers):
        for peer in peers:
            labels = [peer[label] for label in self.labels]

            last_labels = self.last_labels.get(peer['public_key'], {})
            if last_labels and labels != last_labels.get('labels'):
                self.handshake_gauge.remove(*last_labels.get('labels'))
                self.received_gauge.remove(*last_labels.get('labels'))
                self.sent_gauge.remove(*last_labels.get('labels'))
                self.active_gauge.remove(*last_labels.get('labels'))

            self.handshake_gauge.labels(*labels).set(peer['last_handshake'])
            self.received_gauge.labels(*labels).set(peer['received'])
            self.sent_gauge.labels(*labels).set(peer['sent'])
            self.active_gauge.labels(*labels).set(peer['active'])

            self.last_labels[peer['public_key']] = {'labels': labels}

    def find_config_file(self, public_key):
        if public_key in self.names:
            return self.names[public_key]

        with open(os.path.join(CLIENTS_DIR), 'r') as f:
            for line in f:
                fields = line.split()
                if public_key == fields[1]:
                    self.names[public_key] = fields[0]
                    return fields[0]

        return ""
