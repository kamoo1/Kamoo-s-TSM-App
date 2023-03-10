import os
import json
import logging

from ah.storage import BinaryFile, TextFile
from ah.models import MapItemStringMarketValueRecords, MapItemStringMarketValueRecord
from ah.defs import SECONDS_IN
from ah import config


class AuctionDB:
    FN_REGION_COMMODITIES = "{region}-commodities.{suffix}"
    FN_CRID_AUCTIONS = "{region}-{crid}-auctions.{suffix}"
    FN_META = "meta-{region}.json"
    MIN_RECORDS_EXPIRES_IN = 60 * SECONDS_IN.DAY
    DEFAULT_USE_COMPRESSION = True

    def __init__(
        self,
        data_path: str,
        records_expires_in: int = config.MARKET_VALUE_RECORD_EXPIRES,
        use_compression: bool = DEFAULT_USE_COMPRESSION,
    ) -> "AuctionDB":
        if records_expires_in < self.MIN_RECORDS_EXPIRES_IN:
            raise ValueError(
                f"records_expires_in must be at least {self.MIN_RECORDS_EXPIRES_IN}"
            )

        self._logger = logging.getLogger(self.__class__.__name__)
        self.data_path = data_path
        self.records_expires_in = records_expires_in
        self.use_compression = use_compression
        self._file = None

    def update_db(
        self, file: BinaryFile, increment: MapItemStringMarketValueRecord, ts_now: int
    ) -> "MapItemStringMarketValueRecords":
        """
        Update db file, return updated records

        """
        if file.exists():
            records_map = MapItemStringMarketValueRecords.from_file(file)
        else:
            records_map = MapItemStringMarketValueRecords()
        n_added_records, n_added_entries = records_map.update_increment(increment)
        n_removed_records = records_map.remove_expired(ts_now - self.records_expires_in)
        records_map.to_file(file)
        self._logger.info(
            f"DB update: {file.file_path}, {n_added_records=} "
            f"{n_added_entries=} {n_removed_records=}"
        )
        return records_map

    def load_db(self, file: BinaryFile) -> "MapItemStringMarketValueRecords":
        if file.exists():
            records_map = MapItemStringMarketValueRecords.from_file(file)
        else:
            records_map = MapItemStringMarketValueRecords()

        return records_map

    def get_db_file(self, region: str, crid: int = None) -> BinaryFile:
        """
        if only region given, get commodities file
        if both region and crid given, get auctions file
        if none given, get meta file
        """
        fn_suffix = "gz" if self.use_compression else "bin"
        if region and crid:
            fn = self.FN_CRID_AUCTIONS.format(
                region=region, crid=crid, suffix=fn_suffix
            )
        elif region:
            fn = self.FN_REGION_COMMODITIES.format(region=region, suffix=fn_suffix)

        else:
            raise ValueError("crid given without region")

        file_path = os.path.join(self.data_path, fn)
        file = BinaryFile(file_path, use_compression=self.use_compression)
        return file

    def get_meta_file(self, region: str) -> TextFile:
        fn = self.FN_META.format(region=region)
        file_path = os.path.join(self.data_path, fn)
        file = TextFile(file_path)
        return file

    def update_meta(
        self,
        file: TextFile,
        start_ts,
        end_ts,
    ) -> None:
        meta = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "duration": end_ts - start_ts,
        }
        content = json.dumps(meta)
        with file.open("w") as f:
            f.write(content)
