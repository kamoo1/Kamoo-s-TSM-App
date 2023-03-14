import time
from logging import getLogger
from typing import Optional, Tuple
import platform
import psutil

from ah.api import BNAPI
from ah.models import (
    AuctionsResponse,
    CommoditiesResponse,
    MapItemStringMarketValueRecord,
    Region,
)
from ah.db import AuctionDB


class TaskManager:
    def __init__(
        self,
        bn_api: BNAPI,
        db: AuctionDB,
    ) -> None:
        self._logger = getLogger(self.__class__.__name__)
        self.bn_api = bn_api
        self.db = db

    def pull_increment(
        self, region: Region, crid: int = None
    ) -> Optional[MapItemStringMarketValueRecord]:
        if crid:
            try:
                resp = AuctionsResponse.from_api(self.bn_api, region, crid)
            except Exception:
                self._logger.exception(
                    f"Failed to request auctions for {region}-{crid}"
                )
                return
        else:
            try:
                resp = CommoditiesResponse.from_api(self.bn_api, region)
            except Exception:
                self._logger.exception(f"Failed to request commodities for {region}")
                return

        increment = MapItemStringMarketValueRecord.from_response(resp)
        return increment

    def update_region_dbs(self, region: Region) -> Tuple[int, int]:
        start_ts = int(time.time())
        crids = self.bn_api.pull_connected_realms_ids(region)
        for crid in crids:
            increment = self.pull_increment(region, crid)
            if increment:
                file = self.db.get_db_file(region, crid=crid)
                self.db.update_db(file, increment, start_ts)

        increment = self.pull_increment(region)
        if increment:
            file = self.db.get_db_file(region)
            self.db.update_db(file, increment, start_ts)

        end_ts = int(time.time())
        return start_ts, end_ts

    def update_region_meta(self, region: Region, start_ts: int, end_ts: int) -> None:
        # update timestamps
        data_update = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "duration": end_ts - start_ts,
        }

        # connected realms data
        data_cr = {}
        cr_resp = self.bn_api.pull_connected_realms(region)
        for cr_id in cr_resp.keys():
            cr_info = cr_resp[cr_id]
            realm_names = [realm["name"] for realm in cr_info["realms"]]
            data_cr[cr_id] = realm_names

        # data for system info
        data_sys = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "load_avg": psutil.getloadavg(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_total": psutil.virtual_memory().total,
        }

        meta = {
            "update": data_update,
            "connected_realms": data_cr,
            "system": data_sys,
        }
        meta_file = self.db.get_meta_file(region)
        self.db.update_meta(meta_file, meta)
