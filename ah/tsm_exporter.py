from typing import List, Set
import logging
import sys
import os
import re


from ah.models import MapItemStringMarketValueRecords, Region
from ah.storage import TextFile
from ah.db import AuctionDB
from ah.api import BNAPI, GHAPI
from ah.cache import Cache
from ah import config


class TSMExporter:
    REALM_EXPORTS = [
        {
            "type": "AUCTIONDB_REALM_DATA",
            "sources": ["auctions"],
            "fields": [
                "itemString",
                "minBuyout",
                "numAuctions",
                "marketValueRecent",
            ],
        },
        {
            "type": "AUCTIONDB_REALM_HISTORICAL",
            "sources": ["auctions"],
            "fields": [
                "itemString",
                "historical",
            ],
        },
        {
            "type": "AUCTIONDB_REALM_SCAN_STAT",
            "sources": ["auctions"],
            "fields": [
                "itemString",
                "marketValue",
            ],
        },
    ]
    COMMODITIES_EXPORT = {
        "type": "AUCTIONDB_REGION_COMMODITY",
        "sources": ["commodities"],
        "fields": [
            "itemString",
            "minBuyout",
            "numAuctions",
            "marketValueRecent",
        ],
    }
    REGION_EXPORTS = [
        {
            "type": "AUCTIONDB_REGION_STAT",
            "sources": ["auctions", "commodities"],
            "fields": [
                "itemString",
                "regionMarketValue",
            ],
        },
        {
            "type": "AUCTIONDB_REGION_HISTORICAL",
            "sources": ["auctions", "commodities"],
            "fields": [
                "itemString",
                "regionHistorical",
            ],
        },
    ]
    TEMPLATE_ROW = 'select(2, ...).LoadData("{data_type}","{region_or_realm}",[[return {{downloadTime={ts},fields={{{fields}}},data={{{data}}}}}]])'
    TEMPLATE_APPDATA = 'select(2, ...).LoadData("APP_INFO","Global",[[return {{version={version},lastSync={last_sync},message={{id=0,msg=""}},news={{}}}}]])'
    NUMERIC_SET = set("0123456789")
    TSM_VERSION = 41200
    _logger = logging.getLogger("TSMExporter")

    def __init__(self, bn_api: BNAPI, db: AuctionDB, export_file: TextFile) -> None:
        self.bn_api = bn_api
        self.db = db
        self.export_file = export_file

    @classmethod
    def find_warcraft_dir_windows(cls) -> str:
        if sys.platform == "win32":
            import winreg
        else:
            raise RuntimeError("Only support windows")
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft",
        )
        path = winreg.QueryValueEx(key, "InstallPath")[0]
        return os.path.normpath(path)

    @classmethod
    def get_tsm_export_path(cls, warcraft_dir: str = None) -> str:
        if not warcraft_dir:
            warcraft_dir = cls.find_warcraft_dir_windows()

        return os.path.join(
            warcraft_dir,
            "Interface",
            "AddOns",
            "TradeSkillMaster_AppHelper",
            "AppData.lua",
        )

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

                if isinstance(value, int):
                    value = cls.baseN(value, 32)
                elif isinstance(value, float):
                    value = str(value)
                elif isinstance(value, str):
                    pass
                else:
                    raise ValueError(f"unsupported type {type(value)}")

                item_data.append(value)

            if is_skip_item:
                cls._logger.debug(f"Skip item {item_string} due to no data.")
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
        with file.open("a", newline="\n", encoding="utf-8") as f:
            f.write(text_out + "\n")

    def export_region(self, region_name: str, realm_names: Set[str]):
        meta_file = self.db.get_meta_file(region_name)
        meta = self.db.load_meta(meta_file)
        if not meta:
            raise ValueError(f"meta file {meta_file} not found or Empty.")
        ts_update_start = meta["start_ts"]
        ts_update_end = meta["end_ts"]

        crs = self.bn_api.pull_connected_realms(region_name)
        region_data = MapItemStringMarketValueRecords()

        for crid, cr in crs.items():
            # find all realms user want to export in a cr group
            realm_names_ = set(realm["name"] for realm in cr["realms"])
            realm_names_export = realm_names & realm_names_

            cr_auction_file = self.db.get_db_file(region_name, crid)
            cr_auction_data = self.db.load_db(cr_auction_file)
            if cr_auction_data:
                region_data.extend(cr_auction_data)
                for export_realm in self.REALM_EXPORTS:
                    for name in realm_names_export:
                        # realms in same cr group share
                        # the same auction house data
                        self.export_append_data(
                            self.export_file,
                            cr_auction_data,
                            export_realm["fields"],
                            export_realm["type"],
                            name,
                            ts_update_start,
                            ts_update_end,
                        )

        region_commodity_file = self.db.get_db_file(region_name)
        region_commodity_data = self.db.load_db(region_commodity_file)
        if region_commodity_data:
            region_data.extend(region_commodity_data)
            self.export_append_data(
                self.export_file,
                region_commodity_data,
                self.COMMODITIES_EXPORT["fields"],
                self.COMMODITIES_EXPORT["type"],
                region_name.upper(),
                ts_update_start,
                ts_update_end,
            )

        if region_data:
            for region_export in self.REGION_EXPORTS:
                self.export_append_data(
                    self.export_file,
                    region_data,
                    region_export["fields"],
                    region_export["type"],
                    region_name.upper(),
                    ts_update_start,
                    ts_update_end,
                )

        self.export_append_app_info(self.export_file, self.TSM_VERSION, ts_update_end)

    @classmethod
    def export_append_app_info(cls, file: TextFile, version: int, ts_last_sync: int):
        # mine windows uses cp936, let's be more explicit here
        # https://docs.python.org/3.10/library/functions.html#open
        with file.open("a", newline="\n", encoding="utf-8") as f:
            text_out = cls.TEMPLATE_APPDATA.format(
                version=version,
                last_sync=ts_last_sync,
            )
            f.write(text_out + "\n")


def main(
    db_path: str = None,
    compress_db: bool = None,
    repo: str = None,
    export_region: Region = None,
    export_realms: Set[str] = None,
    export_path: str = None,
    bn_api: BNAPI = None,
    cache: Cache = None,
):
    if cache is None:
        cache_path = os.path.join(config.TEMP_PATH, config.APP_NAME + "_cache")
        cache = Cache(cache_path)

    if bn_api is None:
        bn_api = BNAPI(
            config.BN_CLIENT_ID,
            config.BN_CLIENT_SECRET,
            cache,
        )

    gh_api = GHAPI(cache)

    if repo:
        mode = AuctionDB.MODE_REMOTE_R
    else:
        mode = AuctionDB.MODE_LOCAL_RW

    db = AuctionDB(
        db_path,
        config.MARKET_VALUE_RECORD_EXPIRES,
        compress_db,
        mode,
        repo,
        gh_api,
    )

    if not export_path:
        export_path = TSMExporter.get_tsm_export_path()

    export_file = TextFile(export_path)
    exporter = TSMExporter(bn_api, db, export_file)
    exporter.export_file.remove()
    exporter.export_region(export_region, export_realms)


if __name__ == "__main__":
    kwargs = {
        "db_path": "./db",
        "compress_db": True,
        "repo": "https://github.com/kamoo1/TSM-Backend",
        "export_region": "tw",
        "export_realms": {"日落沼澤"},
    }
    main(**kwargs)
