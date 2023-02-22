import time
import threading

from settings import *
from prometheus_client import generate_latest


class MetricsCache(threading.Thread):
    def __init__(self, wireguard_collector):
        super().__init__()
        self.wireguard_exporter = wireguard_collector
        self.cache = None
        self.shutdown_event = threading.Event()
        self.cache_lock = threading.Lock()

    def run(self):
        while not self.shutdown_event.is_set():
            self.wireguard_exporter.collect_metrics()
            cache = generate_latest()

            with self.cache_lock:
                self.cache = cache

            time.sleep(UPDATE_CACHE_TIME)

    def retrieve_cache(self):
        with self.cache_lock:
            return self.cache

    def stop(self):
        self.shutdown_event.set()
