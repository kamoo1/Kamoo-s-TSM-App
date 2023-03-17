import sys
import logging
import argparse
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
    RegionEnum,
    Namespace,
    DBTypeEnum,
    NameSpaceCategoriesEnum,
    GameVersionEnum,
)
from ah.db import AuctionDB
from ah import config
from ah.cache import Cache


class Updater:
    def __init__(
        self,
        bn_api: BNAPI,
        db: AuctionDB,
    ) -> None:
        self._logger = getLogger(self.__class__.__name__)
        self.bn_api = bn_api
        self.db = db

    def pull_increment(
        self, region: RegionEnum, crid: int = None
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

    def update_region_dbs(self, namespace: Namespace) -> Tuple[int, int]:
        start_ts = int(time.time())
        crids = self.bn_api.pull_connected_realms_ids(namespace.region)
        for crid in crids:
            increment = self.pull_increment(namespace.region, crid)
            if increment:
                file = self.db.get_file(namespace, DBTypeEnum.AUCTIONS, crid=crid)
                self.db.update_db(file, increment, start_ts)

        increment = self.pull_increment(namespace.region)
        if increment:
            file = self.db.get_file(namespace, DBTypeEnum.COMMODITIES)
            self.db.update_db(file, increment, start_ts)

        end_ts = int(time.time())
        return start_ts, end_ts

    def update_region_meta(
        self, namespace: Namespace, start_ts: int, end_ts: int
    ) -> None:
        # update timestamps
        data_update = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "duration": end_ts - start_ts,
        }

        # connected realms data
        data_cr = {}
        cr_resp = self.bn_api.pull_connected_realms(namespace.region)
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
        meta_file = self.db.get_file(namespace, DBTypeEnum.META)
        self.db.update_meta(meta_file, meta)


def main(
    db_path: str = None,
    game_version: GameVersionEnum = None,
    region: RegionEnum = None,
    cache: Cache = None,
    bn_api: BNAPI = None,
):
    if bn_api is None:
        if cache is None:
            cache_path = config.DEFAULT_CACHE_PATH
            cache = Cache(cache_path)
        bn_api = BNAPI(
            config.BN_CLIENT_ID,
            config.BN_CLIENT_SECRET,
            cache,
        )
    db = AuctionDB(
        db_path, config.MARKET_VALUE_RECORD_EXPIRES, config.DEFAULT_DB_COMPRESS
    )
    namespace = Namespace(
        category=NameSpaceCategoriesEnum.DYNAMIC,
        game_version=game_version,
        region=region,
    )
    task_manager = Updater(bn_api, db)
    start_ts, end_ts = task_manager.update_region_dbs(namespace)
    task_manager.update_region_meta(namespace, start_ts, end_ts)


def parse_args(raw_args):
    parser = argparse.ArgumentParser()
    default_db_path = config.DEFAULT_DB_PATH
    default_game_version = GameVersionEnum.RETAIL.name.lower()
    parser.add_argument(
        "--db_path",
        help=f"Path to database, default: {default_db_path!r}",
        default=default_db_path,
        type=str,
    )
    parser.add_argument(
        "--game_version",
        choices={e.name.lower() for e in GameVersionEnum},
        default=default_game_version,
        help=f"Game version to export, default: {default_game_version!r}",
    )
    parser.add_argument(
        "region",
        choices={e.value for e in RegionEnum},
        help="Region to export",
    )
    args = parser.parse_args(raw_args)
    args.game_version = GameVersionEnum[args.game_version.upper()]
    args.region = RegionEnum(args.region)
    return args


if __name__ == "__main__":
    logging.basicConfig(level=config.LOGGING_LEVEL)
    args = parse_args(sys.argv[1:])
    main(**vars(args))
