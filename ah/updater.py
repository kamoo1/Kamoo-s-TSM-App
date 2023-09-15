import sys
import logging
import argparse
import time
from logging import getLogger
from typing import Optional, Tuple
import platform
import psutil

from ah.api import BNAPI, GHAPI
from ah.models import (
    AuctionsResponse,
    CommoditiesResponse,
    MapItemStringMarketValueRecord,
    RegionEnum,
    Namespace,
    DBTypeEnum,
    NameSpaceCategoriesEnum,
    GameVersionEnum,
    FactionEnum,
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
        self, namespace: Namespace, crid: int = None, faction: FactionEnum = None
    ) -> Optional[MapItemStringMarketValueRecord]:
        if crid:
            try:
                resp = AuctionsResponse.from_api(
                    self.bn_api, namespace, crid, faction=faction
                )
            except Exception:
                self._logger.warning(
                    f"Failed to request auctions for {namespace} {crid} {faction!s}",
                    exc_info=True,
                )
                return
        else:
            try:
                resp = CommoditiesResponse.from_api(self.bn_api, namespace)
            except Exception:
                self._logger.warning(
                    f"Failed to request commodities for {namespace}",
                    exc_info=True,
                )
                return

        increment = MapItemStringMarketValueRecord.from_response(
            resp, namespace.game_version
        )
        return increment

    def update_region_dbs(self, namespace: Namespace) -> Tuple[int, int]:
        start_ts = int(time.time())
        crids = self.bn_api.pull_connected_realms_ids(namespace)
        if namespace.game_version == GameVersionEnum.RETAIL:
            factions = [None]
        else:
            factions = [FactionEnum.ALLIANCE, FactionEnum.HORDE]

        for crid in crids:
            for faction in factions:
                # NOTE: present in last api, but can't fetch auctions here.
                # (tw vanilla) 5299 5301
                # (tw wlk)     5744
                increment = self.pull_increment(
                    namespace,
                    crid=crid,
                    faction=faction,
                )
                if increment:
                    file = self.db.get_file(
                        namespace,
                        DBTypeEnum.AUCTIONS,
                        crid=crid,
                        faction=faction,
                    )
                    self.db.update_db(file, increment, start_ts)

        if namespace.game_version == GameVersionEnum.RETAIL:
            increment = self.pull_increment(namespace)
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
        # NOTE: listed in first api, but can't fetch the details in the second api.
        # (tw vanilla) 5299
        # (tw wlk)     5744
        cr_resp = self.bn_api.pull_connected_realms(namespace)
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
    repo: str = None,
    gh_proxy: str = None,
    game_version: GameVersionEnum = None,
    region: RegionEnum = None,
    # below are for testability
    cache: Cache = None,
    gh_api: GHAPI = None,
    bn_api: BNAPI = None,
):
    cache = cache or Cache(config.DEFAULT_CACHE_PATH)
    if repo:
        mode = AuctionDB.MODE_REMOTE_R_LOCAL_RW
        gh_api = gh_api or GHAPI(cache, gh_proxy)
    else:
        mode = AuctionDB.MODE_LOCAL_RW

    bn_api = bn_api or BNAPI(
        config.BN_CLIENT_ID,
        config.BN_CLIENT_SECRET,
        cache,
    )
    db = AuctionDB(
        db_path,
        config.MARKET_VALUE_RECORD_EXPIRES,
        config.DEFAULT_DB_COMPRESS,
        mode=mode,
        fork_repo=repo,
        gh_api=gh_api,
    )
    namespace = Namespace(
        category=NameSpaceCategoriesEnum.DYNAMIC,
        game_version=game_version,
        region=region,
    )
    task_manager = Updater(bn_api, db)
    start_ts, end_ts = task_manager.update_region_dbs(namespace)
    task_manager.update_region_meta(namespace, start_ts, end_ts)
    task_manager._logger.info(f"Updated {namespace}")


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
        "--repo",
        type=str,
        default=None,
        help="Address of Github repo that's hosting the db files. If given, "
        "download and use repo's db if local does not exist, "
        "otherwise use local db straight away. ",
    )
    parser.add_argument(
        "--gh_proxy",
        type=str,
        default=None,
        help="URL of Github proxy server, for people having trouble accessing Github "
        "while using --repo option. "
        "Read more at https://github.com/crazypeace/gh-proxy, "
        "this program need a modified version that hosts API requests: "
        "https://github.com/hunshcn/gh-proxy/issues/44",
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

    if args.repo and not AuctionDB.validate_repo(args.repo):
        raise ValueError(
            f"Invalid Github repo given by '--repo' option, "
            f"it should be a valid Github repo URL, not {args.repo!r}."
        )
    if args.repo and args.gh_proxy and not GHAPI.validate_gh_proxy(args.gh_proxy):
        raise ValueError(
            f"Invalid Github proxy server given by '--gh_proxy' option, "
            f"it should be a valid URL, not {args.gh_proxy!r}."
        )
    args.game_version = GameVersionEnum[args.game_version.upper()]
    args.region = RegionEnum(args.region)
    return args


if __name__ == "__main__":
    logging.basicConfig(level=config.LOGGING_LEVEL)
    args = parse_args(sys.argv[1:])
    main(**vars(args))
