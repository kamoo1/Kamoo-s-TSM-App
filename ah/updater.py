import re
import sys
import time
import logging
import argparse
from logging import getLogger
from typing import Tuple
from requests.exceptions import HTTPError

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
    MapItemStringMarketValueRecords,
    ConnectedRealm,
    Meta,
    MarketValueRecords,
)
from ah.storage import BinaryFile
from ah.db import DBHelper, GithubFileForker
from ah import config
from ah.cache import Cache
from ah.sysinfo import SysInfo


class Updater:
    RECORDS_EXPIRES_IN = config.MIN_RECORD_EXPIRES

    def __init__(
        self,
        bn_api: BNAPI,
        db_helper: DBHelper,
        forker: GithubFileForker = None,
    ) -> None:
        self._logger = getLogger(self.__class__.__name__)
        self.bn_api = bn_api
        self.db_helper = db_helper
        self.forker = forker

    def pull_increment(
        self,
        namespace: Namespace,
        connected_realm_id: int = None,
        faction: FactionEnum = None,
    ) -> MapItemStringMarketValueRecord:
        """pull lastest auction increment from api, if `connected_realm_id`
        not given, then pull commodities (retail commodities are region-wide).

        NOTE: failed to fetch auctions for some connected realms,
              due to `auctions` field being `None` or a 404 status code.

              we will return a falsy increment in case of `auctions` field being `None`,
              or returning `None` when 404. together with warning log message.

        """
        if connected_realm_id:
            try:
                resp = AuctionsResponse.from_api(
                    self.bn_api, namespace, connected_realm_id, faction=faction
                )
            except HTTPError as e:
                self._logger.warning(
                    "Failed to request auctions for: "
                    f"{namespace!r} {connected_realm_id} {faction!s}. "
                    f"Error message: {e!s}"
                )
                self._logger.debug("traceback:", exc_info=True)
                return MapItemStringMarketValueRecord()

            if not resp.get_auctions():
                self._logger.warning(
                    "Requested auction was empty: "
                    f"{namespace!r} {connected_realm_id} {faction!s}",
                )

        else:
            try:
                resp = CommoditiesResponse.from_api(self.bn_api, namespace)
            except HTTPError as e:
                self._logger.warning(
                    f"Failed to request commodities for: {namespace=!r}. "
                    f"Error message: {e!s}"
                )
                self._logger.debug("traceback:", exc_info=True)
                return MapItemStringMarketValueRecord()

            if not resp.get_auctions():
                self._logger.warning(
                    f"Requested commodities was empty: {namespace!r}",
                )

        increment = MapItemStringMarketValueRecord.from_response(
            resp, namespace.game_version
        )

        return increment

    def save_increment(
        self,
        file: BinaryFile,
        increment: MapItemStringMarketValueRecord,
        start_ts: int,
        ts_compressed: int = 0,
        is_tsc_local: bool = False,
    ) -> MapItemStringMarketValueRecords:
        if file.exists() != is_tsc_local:
            # db file and db compress ts locality does not match
            # note in case of local mode + meta miss + data miss, the locality of
            # meta and data did match. but `ts_compress` is still 0 due to blank
            # `Meta`, due to local miss and forker is `None`.
            self._logger.debug(
                "`ts_compress` set to 0: "
                f"{is_tsc_local=!r}, "
                f"{file!r}.exists()={file.exists()!r}"
            )
            ts_compressed = 0

        records = MapItemStringMarketValueRecords.from_file(file, forker=self.forker)
        n_added_records, n_added_entries = records.update_increment(increment)
        n_removed_records = records.remove_expired(start_ts - self.RECORDS_EXPIRES_IN)
        n_removed_records += records.compress(
            start_ts,
            self.RECORDS_EXPIRES_IN,
            ts_compressed=ts_compressed,
        )
        records.to_file(file)
        self._logger.info(
            f"DB update: {file!r}, {n_added_records=} "
            f"{n_added_entries=} {n_removed_records=}"
        )
        return records

    def update_region_records(
        self,
        namespace: Namespace,
        connected_realm_ids: Tuple[int],
        ts_compressed: int = 0,
        is_tsc_local: bool = False,
    ) -> Tuple[int, int]:
        """update auction / commodities records for every connected realm under
        this region

        returns update start_ts and end_ts
        """
        start_ts = int(time.time())
        if namespace.game_version == GameVersionEnum.RETAIL:
            factions = [None]
        else:
            factions = [FactionEnum.ALLIANCE, FactionEnum.HORDE]

        for crid in connected_realm_ids:
            for faction in factions:
                increment = self.pull_increment(
                    namespace,
                    connected_realm_id=crid,
                    faction=faction,
                )
                file = self.db_helper.get_file(
                    namespace,
                    DBTypeEnum.AUCTIONS,
                    crid=crid,
                    faction=faction,
                )
                self.save_increment(
                    file,
                    increment,
                    start_ts,
                    ts_compressed=ts_compressed,
                    is_tsc_local=is_tsc_local,
                )

        if namespace.game_version == GameVersionEnum.RETAIL:
            increment = self.pull_increment(namespace)
            file = self.db_helper.get_file(namespace, DBTypeEnum.COMMODITIES)
            self.save_increment(
                file,
                increment,
                start_ts,
                ts_compressed=ts_compressed,
                is_tsc_local=is_tsc_local,
            )

        # just in case we're in the same ts as the increment, which cause
        # `MarketValueRecords.average_by_day` to ignore the increment record
        # because the ts passed in is the same as the increment's ts
        end_ts = int(time.time()) + 1
        return start_ts, end_ts

    def pull_region_meta(self, namespace: Namespace) -> Meta:
        """get latest connected realm info for this region"""
        meta = Meta()
        crids = []
        resp = self.bn_api.get_connected_realms_index(namespace)
        for cr in resp["connected_realms"]:
            match = re.search(r"connected-realm/(\d+)", cr["href"])
            crid = match.group(1)
            crids.append(int(crid))

        for crid in crids:
            try:
                connected_realm = ConnectedRealm.from_api(self.bn_api, namespace, crid)
            except HTTPError as e:
                """
                NOTE: some of the connected realms fails with a 404 status code.

                """
                self._logger.warning(
                    "Failed to request connected realm data for: "
                    f"{namespace!r} {crid}. "
                    f"Error message: {e!s}"
                )
                self._logger.debug("traceback:", exc_info=True)
            else:
                meta.add_connected_realm(crid, connected_realm)

        return meta

    def update_region(self, namespace: Namespace, compress_all=False) -> None:
        sys_info = SysInfo()
        sys_info.begin_monitor()
        # get compress time from last start_ts
        meta_file = self.db_helper.get_file(namespace, DBTypeEnum.META)
        if meta_file.exists():
            is_tsc_local = True
        else:
            is_tsc_local = False
        meta = Meta.from_file(meta_file, forker=self.forker)
        last_start_ts = meta.get_update_ts()[0]
        if compress_all:
            self._logger.info("compress_all is True, set `ts_compress` to 0")
            ts_compressed = 0
        elif last_start_ts:
            ts_compressed = MarketValueRecords.get_compress_end_ts(last_start_ts)
        else:
            self._logger.debug("meta file does not exist, set `ts_compress` to 0")
            ts_compressed = 0

        # create latest meta
        meta = self.pull_region_meta(namespace)
        start_ts, end_ts = self.update_region_records(
            namespace,
            meta.get_connected_realm_ids(),
            ts_compressed=ts_compressed,
            is_tsc_local=is_tsc_local,
        )
        meta.set_update_ts(start_ts, end_ts)
        sys_info.stop_monitor()
        meta.set_system(sys_info.get_sysinfo())
        meta.to_file(meta_file)


def main(
    db_path: str = None,
    repo: str = None,
    gh_proxy: str = None,
    game_version: GameVersionEnum = None,
    region: RegionEnum = None,
    compress_all: bool = False,
    # below are for testability
    cache: Cache = None,
    gh_api: GHAPI = None,
    bn_api: BNAPI = None,
):
    cache = cache or Cache(config.DEFAULT_CACHE_PATH)
    cache.remove_expired()

    if repo:
        gh_api = gh_api or GHAPI(cache, gh_proxy)
        forker = GithubFileForker(repo, gh_api)
    else:
        forker = None

    bn_api = bn_api or BNAPI(
        config.BN_CLIENT_ID,
        config.BN_CLIENT_SECRET,
        cache,
    )
    namespace = Namespace(
        category=NameSpaceCategoriesEnum.DYNAMIC,
        game_version=game_version,
        region=region,
    )
    db_helper = DBHelper(db_path)
    updater = Updater(bn_api, db_helper, forker=forker)
    updater.update_region(namespace, compress_all=compress_all)
    updater._logger.info(f"Updated {namespace!r}")


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
        "--compress_all",
        action="store_true",
        help="ignore `ts_compress`, compress all records even if they have already "
        "been compressed. In case of errors caused by `ts_compress` being "
        "incorrect, use this option to fix it.",
    )
    parser.add_argument(
        "region",
        choices={e.value for e in RegionEnum},
        help="Region to export",
    )
    args = parser.parse_args(raw_args)

    if args.repo and not GithubFileForker.validate_repo(args.repo):
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
