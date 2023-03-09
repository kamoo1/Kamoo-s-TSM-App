from typing import List
import logging

from ah.models.self import MapItemStringMarketValueRecords, ItemString
from ah.storage import TextFile


class TSMExporter:
    TEMPLATE = 'select(2, ...).LoadData("{data_type}","{region_or_realm}",[[return {{downloadTime={ts},fields={{{fields}}},data={{{data}}}}}]])'
    NUMERIC_SET = set("0123456789")
    _logger = logging.getLogger("TSMExporter")

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
