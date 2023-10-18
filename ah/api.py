from __future__ import annotations
import logging
import requests
from requests.adapters import HTTPAdapter, Retry
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
from enum import Enum

from semver import Version

from ah import config, __version__
from ah.vendors.blizzardapi import BlizzardApi
from ah.models import Namespace
from ah.cache import bound_cache, BoundCacheMixin, Cache
from ah.defs import SECONDS_IN

__all__ = (
    "BNAPI",
    "GHAPI",
    "UpdateEnum",
)


class BNAPI(BoundCacheMixin):
    def __init__(
        self, client_id: str, client_secret: str, cache: Cache, *args, **kwargs
    ) -> None:
        super().__init__(*args, cache=cache, **kwargs)
        self._api = BlizzardApi(client_id, client_secret)

    @bound_cache(SECONDS_IN.WEEK)
    def get_connected_realms_index(self, namespace: Namespace) -> Any:
        return self._api.wow.game_data.get_connected_realms_index(
            namespace.region, namespace.get_locale(), namespace.to_str()
        )

    @bound_cache(SECONDS_IN.WEEK)
    def get_connected_realm(self, namespace: Namespace, connected_realm_id: int) -> Any:
        return self._api.wow.game_data.get_connected_realm(
            namespace.region,
            namespace.get_locale(),
            namespace.to_str(),
            connected_realm_id,
        )

    @bound_cache(SECONDS_IN.HOUR)
    def get_auctions(
        self,
        namespace: Namespace,
        connected_realm_id: int,
        auction_house_id: int = None,
    ) -> Any:
        return self._api.wow.game_data.get_auctions(
            namespace.region,
            namespace.get_locale(),
            namespace.to_str(),
            connected_realm_id,
            auction_house_id=auction_house_id,
        )

    @bound_cache(SECONDS_IN.HOUR)
    def get_commodities(self, namespace: Namespace) -> Any:
        return self._api.wow.game_data.get_commodities(
            namespace.region,
            namespace.get_locale(),
            namespace.to_str(),
        )


class UpdateEnum(Enum):
    NONE = 0
    OPTIONAL = 1
    REQUIRED = 2


class GHAPI(BoundCacheMixin):
    REQUESTS_KWARGS = {"timeout": 10}
    RELEASED_ARCHIVE_NAME = config.RELEASED_ARCHIVE_NAME
    logger = logging.getLogger("GHAPI")

    def __init__(self, cache: Cache, gh_proxy=None) -> None:
        self.gh_proxy = gh_proxy
        if self.gh_proxy and self.gh_proxy[-1] != "/":
            self.gh_proxy += "/"
        self.session = requests.Session()
        # note: sometimes /tags returns 403
        retries = Retry(
            total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504, 403]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        super().__init__(cache=cache)

    @classmethod
    def validate_gh_proxy(cls, gh_proxy: str) -> None:
        if not gh_proxy:
            return False

        try:
            result = urlparse(gh_proxy)
            return all(
                [result.scheme, result.netloc, result.scheme in ["http", "https"]]
            )

        except Exception:
            return False

    def add_proxy(self, url: str):
        if self.gh_proxy:
            return self.gh_proxy + url
        return url

    @bound_cache(10 * SECONDS_IN.MIN)
    def get_assets_uri(
        self,
        user: str,
        repo: str,
        tag: str = "latest",
    ) -> Dict[str, str]:
        self.logger.info(f"Fetching assets list from release {tag!r}")
        url = f"https://api.github.com/repos/{user}/{repo}/releases/tags/{tag}"
        url = self.add_proxy(url)
        resp = self.session.get(
            url,
            **self.REQUESTS_KWARGS,
        )
        if resp.status_code != 200:
            raise ValueError(f"Failed to get latest releases, code: {resp.status_code}")
        d = resp.json()
        release_id = d["id"]

        ret = {}
        page = 0
        per_page = 100
        while True:
            page += 1
            url = (
                f"https://api.github.com/repos/{user}/{repo}/"
                f"releases/{release_id}/assets?page={page}&per_page={per_page}"
            )
            url = self.add_proxy(url)
            resp = self.session.get(
                url,
                **self.REQUESTS_KWARGS,
            )
            if resp.status_code != 200:
                raise ValueError(
                    f"Failed to get latest release assets, code: {resp.status_code}"
                )

            assets = resp.json()
            for asset in assets:
                ret[asset["name"]] = asset["browser_download_url"]

            if len(assets) < per_page:
                break

        return ret

    @bound_cache(10 * SECONDS_IN.MIN)
    def get_asset(self, url: str) -> bytes:
        name = urlparse(url).path.split("/")[-1]
        self.logger.info(f"Downloading asset {name!r}")
        url = self.add_proxy(url)
        resp = self.session.get(url, **self.REQUESTS_KWARGS)
        if resp.status_code != 200:
            raise ValueError(f"Failed to get releases, code: {resp.status_code}")
        return resp.content

    @bound_cache(10 * SECONDS_IN.MIN)
    def get_tags(self, user: str, repo: str) -> List[str]:
        self.logger.info(f"Fetching tags from {repo!r}")
        url = f"https://api.github.com/repos/{user}/{repo}/tags"
        url = self.add_proxy(url)
        resp = self.session.get(url, **self.REQUESTS_KWARGS)
        if resp.status_code != 200:
            raise ValueError(f"Failed to get tags, code: {resp.status_code}")
        tags = resp.json()
        return [tag["name"] for tag in tags]

    def get_versions(self, user: str, repo: str) -> List[Version]:
        ret = []
        for tag in self.get_tags(user, repo):
            tag = tag.lstrip("v")
            try:
                ret.append(Version.parse(tag))
            except ValueError:
                pass

        return ret

    def get_latest_version(self, user: str, repo: str) -> Version | None:
        versions = self.get_versions(user, repo)
        if not versions:
            return None

        # filter out pre-releases
        versions = [ver for ver in versions if not ver.prerelease]

        return max(versions)

    def check_update(
        self, user: str, repo: str, current_ver: str | Version | None = None
    ) -> Tuple[UpdateEnum, Version | None]:
        if current_ver is None:
            current_ver = Version.parse(__version__)

        if isinstance(current_ver, str):
            current_ver = current_ver.lstrip("v")
            current_ver = Version.parse(current_ver)

        latest_version = self.get_latest_version(user, repo)
        if not latest_version or latest_version <= current_ver:
            return UpdateEnum.NONE, latest_version

        if latest_version.major > current_ver.major:
            return UpdateEnum.REQUIRED, latest_version

        else:
            return UpdateEnum.OPTIONAL, latest_version

    def get_build_release(self, user: str, repo: str, ver: str | Version) -> bytes:
        if isinstance(ver, str):
            ver = ver.lstrip("v")
            ver = Version.parse(ver)

        tag = f"v{ver}"
        assets = self.get_assets_uri(user, repo, tag=tag)
        if self.RELEASED_ARCHIVE_NAME not in assets:
            msg = f"Failed to find {self.RELEASED_ARCHIVE_NAME!r} in release {tag!r}"
            raise ValueError(msg)

        return self.get_asset(assets[self.RELEASED_ARCHIVE_NAME])
