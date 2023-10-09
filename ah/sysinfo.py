import platform
import psutil
import threading
import logging

from ah import config


class SysInfo:
    SNAPSHOT_INTERVAL = config.DEFAULT_SNAPSHOT_INTERVAL
    MAX_SNAPSHOTS = config.MAX_SNAPSHOTS
    _logger = logging.getLogger(__name__)

    def __init__(self):
        self._sysinfo = {
            "specs": self._collect_specs(),
            "snapshots": None,
        }
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def _collect_specs(self):
        basics = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
        }
        return basics

    # collects cpu / memory periodically in a thread
    def begin_monitor(self):
        self._monitor_thread = threading.Thread(target=self._monitor)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def stop_monitor(self):
        self._stop_event.set()
        self._monitor_thread.join()
        self._stop_event.clear()
        self._monitor_thread = None

    def _snapshot(self):
        return {
            "cpu": psutil.cpu_percent(),
            "mem": psutil.virtual_memory().percent,
        }

    def _monitor(self):
        self._logger.info("begin monitoring")
        snapshots = []
        while True:
            snapshots.append(self._snapshot())
            if len(snapshots) > self.MAX_SNAPSHOTS:
                snapshots.pop(0)
            if self._stop_event.wait(self.SNAPSHOT_INTERVAL):
                break

        self._sysinfo["snapshots"] = snapshots
        self._logger.info(f"stop monitoring, collected {len(snapshots)} snapshots")

    def get_sysinfo(self):
        return self._sysinfo
