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
    DBFileName,
    Namespace,
    DBExtEnum,
    DBTypeEnum,
    DBType,
    GameVersionEnum,
)
from ah.defs import SECONDS_IN
from typing import Dict, Optional, Any
from ah import config

__all__ = ("AuctionDB",)


class AuctionDB:
    MIN_RECORDS_EXPIRES_IN = 60 * SECONDS_IN.DAY
    DEFAULT_USE_COMPRESSION = True
    REPO_MATCHER = re.compile(
        r"^(:?https://)?github.com/(?P<user>[^/]+)/(?P<repo>[^/]+).*$"
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
                f"records_expires_in must be at least {self.MIN_RECORDS_EXPIRES_IN!r}"
            )
        if mode not in (
            self.MODE_LOCAL_RW,
            self.MODE_LOCAL_REMOTE_RW,
            self.MODE_REMOTE_R,
        ):
            raise ValueError(f"Invalid mode: {mode!r}")

        if mode in (self.MODE_LOCAL_REMOTE_RW, self.MODE_REMOTE_R):
            if not (fork_repo and gh_api):
                # verify fork_repo with REPO_MATCHER
                raise ValueError(
                    f"fork_repo and gh_api must be provided when mode is {mode!r}"
                )

            if not self.validate_repo(fork_repo):
                raise ValueError(f"Invalid fork_repo: {fork_repo!r}")

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
        n_removed_records += records_map.compress(ts_now, self.records_expires_in)
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

    # TODO: maybe add `str` overload for all methods
    # having `Basefile` in their signature?
    def fork_file(self, file: BaseFile) -> None:
        try:
            assets = self.pull_assets_url()
        except Exception as e:
            raise RuntimeError(
                f"Failed to download asset map from {self.fork_repo!r}"
            ) from e

        if file.file_name not in assets:
            raise FileNotFoundError(f"File not listed in assets: {file.file_name!r}")

        asset_url = assets[file.file_name]
        self._logger.info(f"Downloading asset {file.file_name!r} from {asset_url!r}")
        try:
            asset_data = self.pull_asset(asset_url)
        except Exception as e:
            raise RuntimeError(
                f"Failed to download asset {file.file_name!r} from {asset_url!r}"
            ) from e


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
        raise NotImplementedError(f"load_db not implemented for {type(file)!r}")

    @load_db.register
    def _(self, file: BinaryFile) -> "MapItemStringMarketValueRecords":
        self.ensure_file(file)
        if file.exists():
            db = MapItemStringMarketValueRecords.from_file(file)
        else:
            db = MapItemStringMarketValueRecords()

        return db

    @load_db.register
    # XXX: test this one, when crid = None
    def _(self, file_name: str) -> "MapItemStringMarketValueRecords":
        file_name_ = DBFileName.from_str(file_name)
        file = self.get_file(
            file_name_.namespace,
            file_name_.db_type.type,
            crid=file_name_.db_type.crid,
        )
        return self.load_db(file)

    def list_file(self):
        candidates = os.listdir(self.data_path)
        ret = []
        for file_name in candidates:
            try:
                DBFileName.from_str(file_name)
            except Exception:
                continue
            file_path = os.path.join(self.data_path, file_name)
            if os.path.isfile(file_path):
                ret.append(file_name)
        return ret

    # XXX: update gh_action
    def get_file(
        self,
        namespace: Namespace,
        db_type_e: DBTypeEnum,
        crid: Optional[int] = None,
    ) -> BaseFile:
        if (
            db_type_e == DBTypeEnum.COMMODITIES
            and namespace.game_version != GameVersionEnum.RETAIL
        ):
            raise ValueError(
                f"Only retail has commodities db, got {namespace.game_version=!r}"
            )

        if db_type_e in (DBTypeEnum.COMMODITIES, DBTypeEnum.META):
            db_type = DBType(type=db_type_e)
        elif db_type_e == DBTypeEnum.AUCTIONS:
            db_type = DBType(type=db_type_e, crid=crid)
        else:
            raise ValueError(f"Invalid `db_type_e` for get_file: {db_type_e!r}")

        if db_type.type == DBTypeEnum.META:
            ext = DBExtEnum.JSON
        else:
            ext = DBExtEnum.GZ if self.use_compression else DBExtEnum.BIN

        file_name = DBFileName(namespace=namespace, db_type=db_type, ext=ext)
        file_path = os.path.join(self.data_path, str(file_name))
        if db_type.type == DBTypeEnum.META:
            file = TextFile(file_path)
        else:
            file = BinaryFile(file_path, use_compression=self.use_compression)

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
                    f"Failed to download {file.file_name!r} from {self.fork_repo!r}"
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
            raise ValueError(f"Invalid mode for update_meta: {self.mode!r}")

        content = json.dumps(meta)
        with file.open("w") as f:
            f.write(content)
