from typing import List, Set, Optional
import argparse
import logging
import sys
import os

import numpy as np

from ah.models import (
    MapItemStringMarketValueRecords,
    RegionEnum,
    Namespace,
    NameSpaceCategoriesEnum,
    GameVersionEnum,
    DBTypeEnum,
    FactionEnum,
    Meta,
)
from ah.storage import TextFile
from ah.db import DBHelper, GithubFileForker
from ah.api import GHAPI
from ah.cache import Cache
from ah import config


class TSMExporter:
    REALM_AUCTIONS_EXPORT = {
        "type": "AUCTIONDB_REALM_DATA",
        "sources": ["realm_auctions"],
        "desc": "realm latest scan data",
        "fields": [
            "itemString",
            "minBuyout",
            "numAuctions",
            "marketValueRecent",
        ],
        "per_faction": True,
    }
    REALM_AUCTIONS_COMMODITIES_EXPORTS = [
        {
            "type": "AUCTIONDB_REALM_HISTORICAL",
            "sources": ["realm_auctions", "commodities"],
            "desc": "realm historical data, realm auction and commodities",
            "fields": [
                "itemString",
                "historical",
            ],
            "per_faction": True,
        },
        {
            "type": "AUCTIONDB_REALM_SCAN_STAT",
            "sources": ["realm_auctions", "commodities"],
            "desc": "realm two week data, realm auction and commodities",
            "fields": [
                "itemString",
                "marketValue",
            ],
            "per_faction": True,
        },
    ]
    COMMODITIES_EXPORT = {
        "type": "AUCTIONDB_REGION_COMMODITY",
        "sources": ["commodities"],
        "desc": "region commodity data",
        "fields": [
            "itemString",
            "minBuyout",
            "numAuctions",
            "marketValueRecent",
        ],
    }
    REGION_AUCTIONS_COMMODITIES_EXPORTS = [
        {
            "type": "AUCTIONDB_REGION_STAT",
            "sources": ["region_auctions", "commodities"],
            "desc": "region two week data, auctions from all realms and commodities",
            "fields": [
                "itemString",
                "regionMarketValue",
            ],
        },
        {
            "type": "AUCTIONDB_REGION_HISTORICAL",
            "sources": ["region_auctions", "commodities"],
            "desc": "region historical data, auctions from all realms and commodities",
            "fields": [
                "itemString",
                "regionHistorical",
            ],
        },
    ]
    TEMPLATE_ROW = (
        'select(2, ...).LoadData("{data_type}","{region_or_realm}",[[return '
        "{{downloadTime={ts},fields={{{fields}}},data={{{data}}}}}]])"
    )
    TEMPLATE_APPDATA = (
        'select(2, ...).LoadData("APP_INFO","Global",[[return '
        "{{version={version},lastSync={last_sync},"
        'message={{id=0,msg=""}},news={{}}}}]])'
    )
    NUMERIC_SET = set("0123456789")
    TSM_VERSION = 41200
    MOCK_WARCRAFT_BASE = "fake_warcraft_base"
    TSM_HC_LABEL = "HC"
    _logger = logging.getLogger("TSMExporter")

    def __init__(
        self,
        db_helper: DBHelper,
        export_file: TextFile,
        forker: GithubFileForker = None,
    ) -> None:
        self.db_helper = db_helper
        self.export_file = export_file
        self.forker = forker

    @classmethod
    def get_tsm_appdata_path(
        cls, warcraft_base: str, game_version: GameVersionEnum
    ) -> str:
        return os.path.join(
            warcraft_base,
            game_version.get_version_folder_name(),
            "Interface",
            "AddOns",
            "TradeSkillMaster_AppHelper",
            "AppData.lua",
        )

    @classmethod
    def find_warcraft_base(cls) -> Optional[str]:
        if "unittest" in sys.modules:
            return cls.MOCK_WARCRAFT_BASE

        if sys.platform == "win32":
            import winreg
        else:
            return None

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft",
        )
        path = winreg.QueryValueEx(key, "InstallPath")[0]
        path = os.path.join(path, "..")
        return os.path.normpath(path)

    @classmethod
    def validate_warcraft_base(cls, path: str) -> bool:
        if not path or not os.path.isdir(path):
            return False

        # at least one version folder should exist
        version_dirs = (
            version.get_version_folder_name() for version in GameVersionEnum
        )
        if not any(
            os.path.isdir(os.path.join(path, version)) for version in version_dirs
        ):
            return False

        return True

    @classmethod
    def baseN(cls, num, b, numerals="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        return ((num == 0) and numerals[0]) or (
            cls.baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b]
        )

    @classmethod
    def export_append_data(
        cls,
        file: TextFile,
        map_records: MapItemStringMarketValueRecords,
        fields: List[str],
        type_: str,
        region_or_realm: str,
        ts_update_begin: int,
        ts_update_end: int,
    ) -> None:
        cls._logger.info(f"Exporting {type_} for {region_or_realm}...")
        items_data = []
        for item_string, records in map_records.items():
            # tsm can handle:
            # 1. numeral itemstring being string
            # 2. 10-based numbers
            item_data = []
            # skip item if all numbers are 0 or None
            is_skip_item = True
            for field in fields:
                if field == "minBuyout":
                    value = records.get_recent_min_buyout(ts_update_begin)
                    if value:
                        is_skip_item = False
                elif field == "numAuctions":
                    value = records.get_recent_num_auctions(ts_update_begin)
                    if value:
                        is_skip_item = False
                elif field == "marketValueRecent":
                    value = records.get_recent_market_value(ts_update_begin)
                    if value:
                        is_skip_item = False
                elif field in ["historical", "regionHistorical"]:
                    value = records.get_historical_market_value(ts_update_end)
                    if value:
                        is_skip_item = False
                elif field in ["marketValue", "regionMarketValue"]:
                    value = records.get_weighted_market_value(ts_update_end)
                    if value:
                        is_skip_item = False
                elif field == "itemString":
                    value = item_string.to_str()
                    if not set(value) < cls.NUMERIC_SET:
                        value = '"' + value + '"'
                else:
                    raise ValueError(f"unsupported field {field}.")

                if isinstance(value, (int, np.int32, np.int64)):
                    value = cls.baseN(value, 32)
                elif isinstance(value, float):
                    value = str(value)
                elif isinstance(value, str):
                    pass
                else:
                    raise ValueError(f"unsupported type {type(value)}")

                item_data.append(value)

            if is_skip_item:
                # XXX: this occurs very often for 15-day and last scan data types,
                # because records outside the time range are still there, therefore
                # the item entry (item string) too.
                # cls._logger.debug(
                #     f"During {type_}, {item_string} skipped, "
                #     f"due to all fields are empty."
                # )
                continue

            item_text = "{" + ",".join(item_data) + "}"
            items_data.append(item_text)

        fields_str = ",".join('"' + field + '"' for field in fields)
        text_out = cls.TEMPLATE_ROW.format(
            data_type=type_,
            region_or_realm=region_or_realm,
            ts=ts_update_begin,
            fields=fields_str,
            data=",".join(items_data),
        )
        with file.open("a", encoding="utf-8") as f:
            f.write(text_out + "\n")

    def export_region(
        self,
        namespace: Namespace,
        export_realms: Set[str],
    ):
        meta_file = self.db_helper.get_file(namespace, DBTypeEnum.META)
        if self.forker:
            meta_file.remove()
        meta = Meta.from_file(meta_file, forker=self.forker)
        if not meta:
            raise ValueError(f"meta file {meta_file} not found or Empty.")
        ts_update_start, ts_update_end = meta.get_update_ts()

        all_realms = set(meta.get_connected_realm_names())
        if not export_realms <= all_realms:
            raise ValueError(f"unavailable realms : {export_realms - all_realms}. ")

        # determines if we need to export hc / non-hc reagional data
        is_exp_regional_hc = is_exp_regional_non_hc = False
        # collect all auction data (non-hc) under this region
        region_auctions_commodities_data = MapItemStringMarketValueRecords()
        # only hc auction data under this region, prices will be vastly different
        region_auctions_data_hc = MapItemStringMarketValueRecords()

        if namespace.game_version == GameVersionEnum.RETAIL:
            commodity_file = self.db_helper.get_file(namespace, DBTypeEnum.COMMODITIES)
            if self.forker:
                commodity_file.remove()
            commodity_data = MapItemStringMarketValueRecords.from_file(
                commodity_file, forker=self.forker
            )
        else:
            commodity_file = None
            commodity_data = None

        if commodity_data:
            # HC doesn't have commodities
            region_auctions_commodities_data.extend(commodity_data)
            self.export_append_data(
                self.export_file,
                commodity_data,
                self.COMMODITIES_EXPORT["fields"],
                self.COMMODITIES_EXPORT["type"],
                namespace.region.upper(),
                ts_update_start,
                ts_update_end,
            )

        if namespace.game_version == GameVersionEnum.RETAIL:
            factions = [None]
        else:
            factions = [FactionEnum.ALLIANCE, FactionEnum.HORDE]

        for crid, connected_realms, is_hc in meta.iter_connected_realms():
            # find all realm names we want to export under this connected realm,
            # they share the same auction data
            sub_export_realms = export_realms & connected_realms

            for faction in factions:
                db_file = self.db_helper.get_file(
                    namespace,
                    DBTypeEnum.AUCTIONS,
                    crid=crid,
                    faction=faction,
                )
                if self.forker:
                    db_file.remove()
                auction_data = MapItemStringMarketValueRecords.from_file(
                    db_file, forker=self.forker
                )
                if not auction_data:
                    self._logger.warning(f"no data in {db_file}.")
                    continue

                if is_hc:
                    region_auctions_data_hc.extend(auction_data)
                else:
                    region_auctions_commodities_data.extend(auction_data)

                if not sub_export_realms:
                    continue
                else:
                    is_exp_regional_hc = is_exp_regional_hc or is_hc
                    is_exp_regional_non_hc = is_exp_regional_non_hc or not is_hc

                if commodity_data:
                    realm_auctions_commodities_data = MapItemStringMarketValueRecords()
                    realm_auctions_commodities_data.extend(commodity_data)
                    realm_auctions_commodities_data.extend(auction_data)
                else:
                    realm_auctions_commodities_data = auction_data

                for realm in sub_export_realms:
                    if faction is None:
                        tsm_realm = realm
                    else:
                        tsm_realm = f"{realm}-{faction.get_full_name()}"

                    self.export_append_data(
                        self.export_file,
                        auction_data,
                        self.REALM_AUCTIONS_EXPORT["fields"],
                        self.REALM_AUCTIONS_EXPORT["type"],
                        tsm_realm,
                        ts_update_start,
                        ts_update_end,
                    )
                    for export_realm in self.REALM_AUCTIONS_COMMODITIES_EXPORTS:
                        self.export_append_data(
                            self.export_file,
                            realm_auctions_commodities_data,
                            export_realm["fields"],
                            export_realm["type"],
                            tsm_realm,
                            ts_update_start,
                            ts_update_end,
                        )

        for data, is_hc_ in zip(
            [region_auctions_commodities_data, region_auctions_data_hc], [False, True]
        ):
            if not data:
                continue

            if is_hc_ and not is_exp_regional_hc:
                continue

            if not is_hc_ and not is_exp_regional_non_hc:
                continue

            region = namespace.region.upper()
            tsm_game_version = (
                self.TSM_HC_LABEL
                if is_hc_
                else namespace.game_version.get_tsm_game_version()
            )
            if tsm_game_version:
                tsm_region = f"{tsm_game_version}-{region}"
            else:
                # retail = None
                tsm_region = region

            # need to sort because it's records are from multiple realms
            # note that we skipped `realm_auctions_commodities_data`, due to
            # no overlapping item strings between auctions and commodities
            data = data.sort()
            for region_export in self.REGION_AUCTIONS_COMMODITIES_EXPORTS:
                self.export_append_data(
                    self.export_file,
                    region_auctions_commodities_data,
                    region_export["fields"],
                    region_export["type"],
                    tsm_region,
                    ts_update_start,
                    ts_update_end,
                )

        self.export_append_app_info(self.export_file, self.TSM_VERSION, ts_update_end)

    @classmethod
    def export_append_app_info(cls, file: TextFile, version: int, ts_last_sync: int):
        with file.open("a", encoding="utf-8") as f:
            text_out = cls.TEMPLATE_APPDATA.format(
                version=version,
                last_sync=ts_last_sync,
            )
            f.write(text_out + "\n")


def main(
    db_path: str = None,
    repo: str = None,
    gh_proxy: str = None,
    game_version: GameVersionEnum = None,
    warcraft_base: str = None,
    export_region: RegionEnum = None,
    export_realms: Set[str] = None,
    # below are for testability
    cache: Cache = None,
    gh_api: GHAPI = None,
):
    if repo:
        cache = cache or Cache(config.DEFAULT_CACHE_PATH)
        cache.remove_expired()
        gh_api = gh_api or GHAPI(cache, gh_proxy=gh_proxy)
        forker = GithubFileForker(db_path, repo, gh_api)
    else:
        forker = None

    db_helper = DBHelper(db_path)
    export_path = TSMExporter.get_tsm_appdata_path(warcraft_base, game_version)
    namespace = Namespace(
        category=NameSpaceCategoriesEnum.DYNAMIC,
        game_version=game_version,
        region=export_region,
    )
    export_file = TextFile(export_path)
    exporter = TSMExporter(db_helper, export_file, forker=forker)
    exporter.export_file.remove()
    exporter.export_region(namespace, export_realms)


def parse_args(raw_args):
    parser = argparse.ArgumentParser()
    default_db_path = config.DEFAULT_DB_PATH
    default_game_version = GameVersionEnum.RETAIL.name.lower()
    default_warcraft_base = TSMExporter.find_warcraft_base()

    parser.add_argument(
        "--db_path",
        type=str,
        default=default_db_path,
        help=f"path to the database, default: {default_db_path!r}",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Address of Github repo that's hosting the db files. If given, "
        "download and use repo's db instead of local ones. "
        "Note: local db will be overwritten.",
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
        "--warcraft_base",
        type=str,
        default=default_warcraft_base,
        help="Path to Warcraft installation directory, "
        "needed if the script is unable to locate it automatically, "
        "should be something like 'C:\\path_to\\World of Warcraft'. "
        f"Auto detect: {default_warcraft_base!r}",
    )
    parser.add_argument(
        "export_region",
        choices={e.value for e in RegionEnum},
        help="Region to export",
    )
    parser.add_argument(
        "export_realms",
        type=str,
        nargs="+",
        help="Realms to export, separated by space.",
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
    if not TSMExporter.validate_warcraft_base(args.warcraft_base):
        raise ValueError(
            "Invalid Warcraft installation directory, "
            "please specify it via '--warcraft_base' option. "
            "Should be something like 'C:\\path_to\\World of Warcraft'."
        )
    args.game_version = GameVersionEnum[args.game_version.upper()]
    args.export_region = RegionEnum(args.export_region)
    args.export_realms = set(args.export_realms)

    return args


if __name__ == "__main__":
    logging.basicConfig(level=config.LOGGING_LEVEL)
    args = parse_args(sys.argv[1:])
    main(**vars(args))
