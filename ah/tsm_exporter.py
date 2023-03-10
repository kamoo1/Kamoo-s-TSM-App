from typing import List
import urllib3
import json
import logging
import sys
import os
import re

if sys.platform == "win32":
    import winreg

from ah.models.self import MapItemStringMarketValueRecords
from ah.storage import TextFile
from ah.fs import ensure_path, get_temp_path
from ah.db import AuctionDB
from ah.api import API


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

    TEMPLATE = 'select(2, ...).LoadData("{data_type}","{region_or_realm}",[[return {{downloadTime={ts},fields={{{fields}}},data={{{data}}}}}]])'
    NUMERIC_SET = set("0123456789")
    ASSET_MATCHER = re.compile(
        r"(?:us|eu|tw|kr)-(?:\d+-auctions|commodities)\.(?:gz|bin)"
    )
    _logger = logging.getLogger("TSMExporter")

    def __init__(self, api: API, db: AuctionDB, export_file: TextFile) -> None:
        self.api = api
        self.db = db
        self.export_file = export_file

    @classmethod
    def download_db(cls, user: str, repo: str, db_path: str) -> None:
        url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
        http = urllib3.PoolManager()
        r = http.request("GET", url)
        data = json.loads(r.data.decode("utf-8"))
        # download url under assets.browser_download_url
        for asset in data["assets"]:
            name = asset["name"]
            if not cls.ASSET_MATCHER.match(name):
                continue
            download_url = asset["browser_download_url"]
            r = http.request("GET", download_url)
            with open(os.path.join(db_path, name), "wb") as f:
                f.write(r.data)

    @classmethod
    def find_warcraft_dir_windows(cls) -> str:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft",
        )
        path = winreg.QueryValueEx(key, "InstallPath")[0]
        return os.path.normpath(path)

    @classmethod
    def locate_line(cls, data: str, pos: int) -> int:
        """Given pos, find start and end of the line where pos is in"""
        start = pos
        end = pos
        while data[start] != "\n":
            start -= 1
        start += 1

        while data[end] != "\n":
            end += 1
        end += 1

        return start, end

    @classmethod
    def baseN(cls, num, b, numerals="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        return ((num == 0) and numerals[0]) or (
            cls.baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b]
        )

    @classmethod
    def append_to_file(
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
                    value = cls.baseN(value, 26)
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
        text_out = cls.TEMPLATE.format(
            data_type=type_,
            region_or_realm=region_or_realm,
            ts=ts_update_begin,
            fields=fields_str,
            data=",".join(items_data),
        )
        with file.open("a", newline="\n") as f:
            f.write(text_out + "\n")

    def export(self, region: str, realms: List[str]):
        region_data = MapItemStringMarketValueRecords()
        crids = self.api.pull_connected_realms_ids(region)
        for crid in crids:
            cr_auction_file = self.db.get_db_file(region, crid)
            cr_auction_data = self.db.load_db(cr_auction_file)
            if cr_auction_data:
                region_data.extend(cr_auction_data)
                for export_realm in self.REALM_EXPORTS:
                    self.append_to_file(
                        self.export_file,
                        cr_auction_data,
                        export_realm["fields"],
                        export_realm["type"],
                        ...,
                        ts_begin,
                        ts_end,
                    )

        region_commodity_file = self.db.get_db_file(region)
        region_commodity_data = self.db.load_db(region_commodity_file)
        if region_commodity_data:
            region_data.extend(region_commodity_data)
            self.append_to_file(...)

        if region_data:
            self.append_to_file(...)


if sys.platform != "win32":
    TSMExporter = None


def main(repo_owner=None, repo_name=None):
    exporter = TSMExporter()
    db_path = os.path.join(get_temp_path(), "ah_db")
    ensure_path(db_path)
    exporter.download_db(repo_owner, repo_name, db_path)


if __name__ == "__main__":
    kwargs = {"repo_owner": "kamoo1", "repo_name": "TSM-Backend"}
    main(**kwargs)
