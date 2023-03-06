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
        update_ts: int,
    ) -> None:
        cls._logger.info(f"Exporting {type_} for {region_or_realm}...")
        items_data = []
        for item_string, records in map_records.items():
            # tsm can handle:
            # 1. numeral itemstring being string
            # 2. 10-based numbers
            item_data = []
            for field in fields:
                if field == "minBuyout":
                    value = records.get_recent_min_buyout()
                elif field == "numAuctions":
                    value = records.get_recent_num_auctions()
                elif field == "marketValueRecent":
                    value = records.get_recent_market_value()
                elif field in ["historical", "regionHistorical"]:
                    value = records.get_historical_market_value(update_ts)
                elif field in ["marketValue", "regionMarketValue"]:
                    value = records.get_weighted_market_value(update_ts)
                elif field == "itemString":
                    value = item_string
                else:
                    raise ValueError(f"unsupported field {field}.")

                if value is None:
                    # TODO: none value, figure out what to do
                    value = "0"
                elif isinstance(value, ItemString):
                    value = value.to_str()
                    # TODO: review set operations
                    if not set(value) < cls.NUMERIC_SET:
                        value = '"' + value + '"'

                elif isinstance(value, int):
                    value = cls.baseN(value, 26)
                elif isinstance(value, float):
                    value = str(value)
                else:
                    raise ValueError(f"unsupported type {type(value)}")

                item_data.append(value)

            item_text = "{" + ",".join(item_data) + "}"
            items_data.append(item_text)

        fields_str = ",".join('"' + field + '"' for field in fields)
        text_out = cls.TEMPLATE.format(
            data_type=type_,
            region_or_realm=region_or_realm,
            ts=update_ts,
            fields=fields_str,
            data=",".join(items_data),
        )
        with file.open("a") as f:
            f.write(text_out + "\n")
