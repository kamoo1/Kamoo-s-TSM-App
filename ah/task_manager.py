import time
from logging import getLogger
from typing import Optional

from ah.api import API
from ah.models import (
    AuctionsResponse,
    CommoditiesResponse,
    MapItemStringMarketValueRecord,
)
from ah.db import AuctionDB


class TaskManager:
    def __init__(
        self,
        api: API,
        db: AuctionDB,
    ) -> None:
        self._logger = getLogger(self.__class__.__name__)
        self.api = api
        self.db = db

    def pull_increment(
        self, region: str, crid: int = None
    ) -> Optional[MapItemStringMarketValueRecord]:
        if crid:
            try:
                resp = AuctionsResponse.from_api(self.api, region, crid)
            except Exception as e:
                self._logger.error(
                    f"Failed to request auctions for {region}-{crid}: {e}"
                )
                return
        else:
            try:
                resp = CommoditiesResponse.from_api(self.api, region)
            except Exception as e:
                self._logger.error(f"Failed to request commodities for {region}: {e}")
                return

        increment = MapItemStringMarketValueRecord.from_response(resp)
        return increment

    def update_dbs_under_region(self, region: str) -> int:
        begin_ts = int(time.time())
        crids = self.api.pull_connected_realms_ids(region)
        for crid in crids:
            increment = self.pull_increment(region, crid)
            if increment:
                file = self.db.get_db_file(region, crid=crid)
                self.db.update_db(file, increment, begin_ts)

        increment = self.pull_increment(region)
        if increment:
            file = self.db.get_db_file(region)
            self.db.update_db(file, increment, begin_ts)

        end_ts = int(time.time())
        meta_file = self.db.get_meta_file(region)
        self.db.update_meta(meta_file, begin_ts, end_ts)
