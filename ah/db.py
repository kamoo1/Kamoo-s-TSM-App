import re
import os
import json
import logging
from functools import singledispatchmethod


from ah.api import GHAPI
from ah.storage import BinaryFile, TextFile, BaseFile
from ah.models import (
    MapItemStringMarketValueRecords,
    MapItemStringMarketValueRecord,
    Region,
)
from ah.defs import SECONDS_IN
from typing import Dict, Optional, Any
from ah import config

__all__ = ("AuctionDB",)


class AuctionDB:
    FN_REGION_COMMODITIES = "{region}-commodities.{suffix}"
    FN_CRID_AUCTIONS = "{region}-{crid}-auctions.{suffix}"
    FN_SUFFIX_GZ = "gz"
    FN_SUFFIX_BIN = "bin"
    FN_META = "meta-{region}.json"
    MIN_RECORDS_EXPIRES_IN = 60 * SECONDS_IN.DAY
    DEFAULT_USE_COMPRESSION = True
    REPO_MATCHER = re.compile(
        r"^(:?https://)?github.com/(?P<user>[^/]+)/(?P<repo>[^/]+).*$"
    )
    __region_regex = Region.get_regex()
    DB_FILE_MATCHER = re.compile(
        rf"^(?:{__region_regex})-(?:\d+-auctions|commodities)\.(?:gz|bin)$"
    )
    # local mode
    MODE_LOCAL_RW = "MODE_LOCAL_RW"
    # fork from repo if not exist, then local mode
    MODE_LOCAL_REMOTE_RW = "MODE_LOCAL_REMOTE_RW"
    # read only from remote
    MODE_REMOTE_R = "MODE_REMOTE_R"

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
        if mode not in (
            self.MODE_LOCAL_RW,
            self.MODE_LOCAL_REMOTE_RW,
            self.MODE_REMOTE_R,
        ):
            raise ValueError(f"Invalid mode: {mode}")

        if mode in (self.MODE_LOCAL_REMOTE_RW, self.MODE_REMOTE_R):
            if not (fork_repo and gh_api):
                # verify fork_repo with REPO_MATCHER
                raise ValueError(
                    f"fork_repo and gh_api must be provided when mode is {mode}"
                )

            if not self.validate_repo(fork_repo):
                raise ValueError(f"Invalid fork_repo: {fork_repo}")

        self._logger = logging.getLogger(self.__class__.__name__)
        self.data_path = data_path
        self.records_expires_in = records_expires_in
        self.use_compression = use_compression
        self.mode = mode
        self.fork_repo = fork_repo
        self.gh_api = gh_api

    @classmethod
    def validate_repo(cls, repo: str) -> Optional[re.Match]:
        return cls.REPO_MATCHER.match(repo)

    @singledispatchmethod
    @classmethod
    def validate_db_name(cls, arg) -> Optional[re.Match]:
        raise NotImplementedError(f"Invalid arg type: {type(arg)}")

    @validate_db_name.register
    @classmethod
    def _(cls, file: BaseFile) -> Optional[re.Match]:
        return cls.DB_FILE_MATCHER.match(file.file_name)

    @validate_db_name.register
    @classmethod
    def _(cls, file_name: str) -> Optional[re.Match]:
        return cls.DB_FILE_MATCHER.match(file_name)

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
        m = self.validate_repo(self.fork_repo)
        if not m:
            raise ValueError(f"Invalid fork_repo: {self.fork_repo}")
        user = m.group("user")
        repo = m.group("repo")
        assets = self.gh_api.get_assets_uri(user, repo)
        return assets

    def pull_asset(self, url) -> bytes:
        return self.gh_api.get_asset(url)

    def fork_file(self, file: BaseFile) -> None:
        try:
            assets = self.pull_assets_url()
        except Exception as e:
            raise RuntimeError(
                f"Failed to get assets info from {self.fork_repo}"
            ) from e

        if file.file_name not in assets:
            raise FileNotFoundError(f"File not listed in assets: {file.file_name}")

        asset_url = assets[file.file_name]
        try:
            asset_data = self.pull_asset(asset_url)
        except Exception as e:
            raise RuntimeError(
                f"Failed to download asset {file.file_name} from {asset_url}"
            ) from e

        self._logger.info(f"Downloaded asset {file.file_name} from {asset_url}")

        # we don't want it to be compressed multiple times
        # since we're essentially doing a copy here.
        if hasattr(file, "use_compression"):
            original_use_compression = file.use_compression
            file.use_compression = False

        with file.open("wb") as f:
            f.write(asset_data)

        if hasattr(file, "use_compression"):
            file.use_compression = original_use_compression

    @singledispatchmethod
    def load_db(self, file) -> "MapItemStringMarketValueRecords":
        raise NotImplementedError(f"load_db not implemented for {type(file)}")

    @load_db.register
    def _(self, file: BinaryFile) -> "MapItemStringMarketValueRecords":
        self.ensure_file(file)
        if file.exists():
            db = MapItemStringMarketValueRecords.from_file(file)
        else:
            db = MapItemStringMarketValueRecords()

        return db

    @load_db.register
    def _(self, file_name: str) -> "MapItemStringMarketValueRecords":
        if file_name.endswith(self.FN_SUFFIX_GZ):
            use_compression = True
        else:
            use_compression = False

        file = BinaryFile(
            os.path.join(self.data_path, file_name),
            use_compression=use_compression,
        )
        return self.load_db(file)

    def list_db_name(self):
        candidates = os.listdir(self.data_path)
        db_names = [fn for fn in candidates if self.validate_db_name(fn)]
        return db_names

    def get_db_file(self, region: Region, crid: int = None) -> BinaryFile:
        """
        if only region given, get commodities file
        if both region and crid given, get auctions file
        """
        fn_suffix = self.FN_SUFFIX_GZ if self.use_compression else self.FN_SUFFIX_BIN
        if region and crid is not None:
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

    def get_meta_file(self, region: Region) -> TextFile:
        fn = self.FN_META.format(region=region)
        file_path = os.path.join(self.data_path, fn)
        file = TextFile(file_path)
        return file

    def ensure_file(self, file: BaseFile) -> None:
        if (
            self.mode == self.MODE_REMOTE_R
            or self.mode == self.MODE_LOCAL_REMOTE_RW
            and not file.exists()
        ):
            try:
                self.fork_file(file)
            except Exception:
                self._logger.exception(
                    f"Failed to download {file.file_name} from {self.fork_repo}"
                )

    def load_meta(self, file: TextFile) -> Dict[str, Any]:
        self.ensure_file(file)
        if file.exists():
            with file.open("r") as f:
                meta = json.load(f)
        else:
            meta = {}

        return meta

    def update_meta(
        self,
        file: TextFile,
        meta: Dict,
    ) -> None:
        if self.mode == self.MODE_REMOTE_R:
            raise ValueError(f"Invalid mode for update_meta: {self.mode}")

        content = json.dumps(meta)
        with file.open("w") as f:
            f.write(content)
