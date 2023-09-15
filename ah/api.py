import re
import requests
from requests.adapters import HTTPAdapter, Retry
from logging import getLogger
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from ah.vendors.blizzardapi import BlizzardApi
from ah.models import Namespace, FactionEnum
from ah.cache import bound_cache, BoundCacheMixin, Cache
from ah.defs import SECONDS_IN

__all__ = (
    "BNAPIWrapper",
    "BNAPI",
    "GHAPI",
)


class BNAPIWrapper(BoundCacheMixin):
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


class BNAPI:
    _logger = getLogger("BNAPI")

    MAP_FACTION_AH_ID = {
        FactionEnum.ALLIANCE: 2,
        FactionEnum.HORDE: 6,
    }

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        cache: Optional[Cache] = None,
        wrapper=None,
        *args,
        **kwargs,
    ) -> None:
        if not wrapper:
            if not all([client_id, client_secret, cache]):
                raise ValueError(
                    "client_id, client_secret and cache must be provided "
                    "if no wrapper is provided."
                )
            self.wrapper = BNAPIWrapper(
                client_id, client_secret, cache, *args, **kwargs
            )
        else:
            self.wrapper = wrapper

    def pull_connected_realms_ids(self, namespace: Namespace) -> Any:
        connected_realms = self.wrapper.get_connected_realms_index(namespace)
        for cr in connected_realms["connected_realms"]:
            ret = re.search(r"connected-realm/(\d+)", cr["href"])
            crid = ret.group(1)
            yield int(crid)

    def pull_connected_realm(self, namespace: Namespace, crid: int) -> Any:
        """
        >>> ret = {
            # crid
            "id": 123,
            "timezone": "Asia/Taipei",
            "realms": [
                {
                    "id": 123,
                    "name": "Realm Name",
                    "slug": "realm-slug"
                },
                ...
            ]
        }
        """
        connected_realm = self.wrapper.get_connected_realm(namespace, crid)
        ret = {"id": crid, "realms": []}
        for realm in connected_realm["realms"]:
            if "timezone" in ret and ret["timezone"] != realm["timezone"]:
                raise ValueError(
                    "Timezone differes between realms under same connected realm!"
                )

            else:
                ret["timezone"] = realm["timezone"]

            ret["realms"].append(
                {
                    "id": realm["id"],
                    "name": realm["name"],
                    "slug": realm["slug"],
                    "locale": realm["locale"],
                }
            )

        return ret

    def pull_connected_realms(self, namespace: Namespace) -> Any:
        """

        >>> {
                # connected realms
                $crid: $crid_data,
                ...
            }
        """
        crids = self.pull_connected_realms_ids(namespace)
        ret = {}
        for crid in crids:
            try:
                connected_realm = self.pull_connected_realm(namespace, crid)
                ret[crid] = connected_realm
            except Exception as e:
                self._logger.error(f"Failed to pull connected realm data {crid}.")
                self._logger.exception(e)

        return ret

    def pull_commodities(self, namespace: Namespace) -> Any:
        commodities = self.wrapper.get_commodities(namespace)
        return commodities

    def pull_auctions(
        self,
        namespace: Namespace,
        crid: int,
        faction: FactionEnum = None,
    ) -> Any:
        auctions = self.wrapper.get_auctions(
            namespace,
            crid,
            auction_house_id=self.MAP_FACTION_AH_ID.get(faction),
        )
        return auctions


class GHAPI(BoundCacheMixin):
    REQUESTS_KWARGS = {"timeout": 10}

    def __init__(self, cache: Cache, gh_proxy=None) -> None:
        self.gh_proxy = gh_proxy
        if self.gh_proxy and self.gh_proxy[-1] != "/":
            self.gh_proxy += "/"
        self.session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
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

    @bound_cache(10 * SECONDS_IN.MIN)
    def get_assets_uri(self, owner: str, repo: str) -> Dict[str, str]:
        url = "https://api.github.com/repos/{user}/{repo}/releases/latest"
        if self.gh_proxy:
            url = self.gh_proxy + url
        resp = self.session.get(
            url.format(user=owner, repo=repo),
            **self.REQUESTS_KWARGS,
        )
        if resp.status_code != 200:
            raise ValueError(f"Failed to get latest releases, code: {resp.status_code}")
        latest_release = resp.json()
        latest_release_id = latest_release["id"]

        ret = {}
        page = 0
        per_page = 100
        while True:
            page += 1
            url = (
                "https://api.github.com/repos/{user}/{repo}/"
                "releases/{release_id}/assets?page={page}&per_page={per_page}"
            )
            resp = self.session.get(
                url.format(
                    user=owner,
                    repo=repo,
                    release_id=latest_release_id,
                    page=page,
                    per_page=per_page,
                ),
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
        if self.gh_proxy:
            url = self.gh_proxy + url
        resp = self.session.get(url, **self.REQUESTS_KWARGS)
        if resp.status_code != 200:
            raise ValueError("Failed to get releases, code: {resp.status_code}")
        return resp.content
