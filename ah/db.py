import re
import os
import json
import logging

import requests

from ah.api import GHAPI
from ah.storage import BinaryFile, TextFile, BaseFile
from ah.models import MapItemStringMarketValueRecords, MapItemStringMarketValueRecord
from ah.defs import SECONDS_IN
from typing import Dict
from ah import config


class AuctionDB:
    FN_REGION_COMMODITIES = "{region}-commodities.{suffix}"
    FN_CRID_AUCTIONS = "{region}-{crid}-auctions.{suffix}"
    FN_META = "meta-{region}.json"
    MIN_RECORDS_EXPIRES_IN = 60 * SECONDS_IN.DAY
    DEFAULT_USE_COMPRESSION = True
    REPO_MATCHER = re.compile(r"github.com/(?P<user>[^/]+)/(?P<repo>[^/]+)")
    # create new if not exist
    MODE_LOCAL_RW = "local"
    # fork from repo if not exist
    MODE_LOCAL_REMOTE_RW = "local_remote"
    # read only from repo
    MODE_REMOTE_R = "remote"

    def __init__(
        self,
        data_path: str,
        records_expires_in: int = config.MARKET_VALUE_RECORD_EXPIRES,
        use_compression: bool = DEFAULT_USE_COMPRESSION,
        mode: str = MODE_LOCAL_RW,
        fork_repo: str = None,
        gh_api: GHAPI = None,
    ) -> "AuctionDB":
        if records_expires_in < self.MIN_RECORDS_EXPIRES_IN:
            raise ValueError(
                f"records_expires_in must be at least {self.MIN_RECORDS_EXPIRES_IN}"
            )
        if mode not in (self.MODE_LOCAL_RW, self.MODE_REMOTE_R):
            raise ValueError(f"Invalid mode: {mode}")

        if mode == self.MODE_REMOTE_R and not (fork_repo and gh_api):
            raise ValueError(
                f"fork_repo and gh_api must be provided when mode is {self.MODE_REMOTE_R}"
            )

        self._logger = logging.getLogger(self.__class__.__name__)
        self.data_path = data_path
        self.records_expires_in = records_expires_in
        self.use_compression = use_compression
        self.mode = mode
        self.fork_repo = fork_repo
        self.gh_api = gh_api

    def update_db(
        self, file: BinaryFile, increment: MapItemStringMarketValueRecord, ts_now: int
    ) -> "MapItemStringMarketValueRecords":
        """
        Update db file, return updated records

        """
        if self.mode == self.MODE_REMOTE_R:
            raise ValueError(f"Invalid mode for update_db: {self.mode}")

        records_map = self.load_db(file)
        n_added_records, n_added_entries = records_map.update_increment(increment)
        n_removed_records = records_map.remove_expired(ts_now - self.records_expires_in)
        records_map.to_file(file)
        self._logger.info(
            f"DB update: {file.file_path}, {n_added_records=} "
            f"{n_added_entries=} {n_removed_records=}"
        )
        return records_map

    def pull_assets_url(self) -> Dict[str, str]:
        # get repo owner, repo name
        m = self.REPO_MATCHER.match(self.fork_repo)
        if not m:
            raise ValueError(f"Invalid fork_repo: {self.fork_repo}")
        user = m.group("user")
        repo = m.group("repo")
        assets = self.gh_api.get_assets_uri(user, repo)
        return assets

    def pull_asset(self, url) -> bytes:
        return self.gh_api.get_asset(url)

    def fork_file(self, file: BaseFile) -> None:
        assets = self.pull_assets_url()
        if file.file_name not in assets:
            raise ValueError(f"File not found in assets: {file.file_name}")
        asset_url = assets[file.file_name]
        self._logger.info(f"Downloading {file.file_name} from {asset_url}")
        asset_data = self.pull_asset(asset_url)
        with file.open("wb") as f:
            f.write(asset_data)

    def load_db(self, file: BinaryFile) -> "MapItemStringMarketValueRecords":
        if (
            self.mode == self.MODE_REMOTE_R
            or self.mode == self.MODE_LOCAL_REMOTE_RW
            and not file.exists()
        ):
            try:
                self.fork_file(file)
            except Exception as e:
                self._logger.error(
                    f"Failed to download db file from {self.fork_repo}: {e}"
                )

        if file.exists():
            db = MapItemStringMarketValueRecords.from_file(file)
        else:
            db = MapItemStringMarketValueRecords()

        return db

    def get_db_file(self, region: str, crid: int = None) -> BinaryFile:
        """
        if only region given, get commodities file
        if both region and crid given, get auctions file
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

    def load_meta(self, file: TextFile):
        if file.exists():
            with file.open("r") as f:
                meta = json.load(f)
        else:
            meta = {}
        return meta

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
