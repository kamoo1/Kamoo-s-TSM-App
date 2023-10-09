from unittest import TestCase
from unittest.mock import patch
import time

from ah.sysinfo import SysInfo


class TestSysInfo(TestCase):
    @patch("ah.sysinfo.SysInfo.SNAPSHOT_INTERVAL", 0.1)
    @patch("ah.sysinfo.SysInfo.MAX_SNAPSHOTS", 2)
    def test_sysinfo(self):
        sysinfo = SysInfo()
        sysinfo.begin_monitor()
        time.sleep(0.5)
        sysinfo.stop_monitor()
        info = sysinfo.get_sysinfo()
        self.assertIn("specs", info)
        self.assertIn("snapshots", info)
        self.assertLessEqual(len(info["snapshots"]), SysInfo.MAX_SNAPSHOTS)
