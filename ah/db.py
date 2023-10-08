from __future__ import annotations
import re
import os
import logging
from typing import TYPE_CHECKING, Dict, Optional

from ah.storage import BinaryFile, TextFile, BaseFile
from ah.models import (
    DBFileName,
    Namespace,
    DBExtEnum,
    DBTypeEnum,
    FactionEnum,
)
from ah.errors import DownloadError
from ah import config

# we only need this for type checking, to avoid circular import
if TYPE_CHECKING:
    from ah.api import GHAPI

__all__ = (
    "DBHelper",
    "GithubFileForker",
)


class GithubFileForker:
    REPO_MATCHER = re.compile(
        r"^(:?https://)?github.com/(?P<user>[^/]+)/(?P<repo>[^/]+).*$"
    )

    def __init__(
        self,
        data_path: str,
        fork_repo: str,
        gh_api: GHAPI,
    ) -> "GithubFileForker":
        if not self.validate_repo(fork_repo):
            raise ValueError(f"Invalid fork_repo: {fork_repo!r}")

        self._logger = logging.getLogger(self.__class__.__name__)
        self._data_path = data_path
        self._fork_repo = fork_repo
        self._gh_api = gh_api

    @classmethod
    # TODO: somewhere used this
    def validate_repo(cls, repo: str) -> Optional[re.Match]:
        return cls.REPO_MATCHER.match(repo)

    def _pull_assets_url(self) -> Dict[str, str]:
        """get a map of asset name to asset url"""
        # get repo owner, repo name
        m = self.validate_repo(self._fork_repo)
        if not m:
            raise ValueError(f"Invalid fork_repo: {self._fork_repo}")
        user = m.group("user")
        repo = m.group("repo")
        assets = self._gh_api.get_assets_uri(user, repo)
        return assets

    def _pull_asset(self, url) -> bytes:
        return self._gh_api.get_asset(url)

    def _fork_file(self, file: BaseFile) -> None:
        try:
            assets = self._pull_assets_url()
        except Exception as e:
            raise DownloadError(
                f"Failed to download asset map from {self._fork_repo!r}"
            ) from e

        if file.file_name not in assets:
            raise DownloadError(f"File not listed in assets: {file.file_name!r}")

        asset_url = assets[file.file_name]
        self._logger.info(f"Downloading asset {file.file_name!r} from {asset_url!r}")
        try:
            asset_data = self._pull_asset(asset_url)
        except Exception as e:
            raise DownloadError(
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

    def ensure_file(self, file: BaseFile) -> None:
        if not file.exists():
            try:
                self._fork_file(file)
            except DownloadError:
                self._logger.warning(
                    f"Failed to download {file.file_name!r} from {self._fork_repo!r}",
                    exc_info=True,
                )


class DBHelper:
    USE_COMPRESSION = config.DEFAULT_DB_COMPRESS

    def __init__(
        self,
        data_path: str,
    ) -> None:
        self._data_path = data_path

    def list_file(self):
        """list db or meta files under data_path"""
        candidates = os.listdir(self._data_path)
        ret = []
        for file_name in candidates:
            try:
                DBFileName.from_str(file_name)
            except Exception:
                continue
            file_path = os.path.join(self._data_path, file_name)
            if os.path.isfile(file_path):
                ret.append(file_name)
        return ret

    def get_file(
        self,
        namespace: Namespace,
        db_type: DBTypeEnum,
        crid: Optional[int] = None,
        faction: Optional[FactionEnum] = None,
    ) -> BaseFile:
        if db_type == DBTypeEnum.META:
            ext = DBExtEnum.JSON
        else:
            ext = DBExtEnum.GZ if self.USE_COMPRESSION else DBExtEnum.BIN

        file_name = DBFileName(
            namespace=namespace,
            db_type=db_type,
            crid=crid,
            faction=faction,
            ext=ext,
        )
        file_path = os.path.join(self._data_path, str(file_name))
        if db_type == DBTypeEnum.META:
            file = TextFile(file_path)
        else:
            file = BinaryFile(file_path, use_compression=self.USE_COMPRESSION)

        return file
