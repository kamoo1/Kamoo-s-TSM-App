import re
from typing import Optional

from ah.vendors.blizzardapi import BlizzardApi
from ah.cache import bound_json_cache, BoundCacheMixin, Cache
from ah.defs import SECONDS_IN


class APIWrapper(BoundCacheMixin):
    def __init__(self, client_id, client_secret, cache: Cache, *args, **kwargs) -> None:
        super().__init__(*args, cache=cache, **kwargs)
        self._api = BlizzardApi(client_id, client_secret)

    @classmethod
    def get_default_locale(cls, region):
        if region == "kr":
            return "ko_KR"
        elif region == "tw":
            return "zh_TW"
        else:
            return "en_US"

    @bound_json_cache(SECONDS_IN.WEEK)
    def get_connected_realms_index(self, region, locale=None):
        if not locale:
            locale = self.get_default_locale(region)
        return self._api.wow.game_data.get_connected_realms_index(region, locale)

    @bound_json_cache(SECONDS_IN.WEEK)
    def get_connected_realm(self, region, connected_realm_id, locale=None):
        if not locale:
            locale = self.get_default_locale(region)
        return self._api.wow.game_data.get_connected_realm(
            region, locale, connected_realm_id
        )

    @bound_json_cache(SECONDS_IN.HOUR)
    def get_auctions(self, region, connected_realm_id, locale=None):
        if not locale:
            locale = self.get_default_locale(region)
        return self._api.wow.game_data.get_auctions(region, locale, connected_realm_id)

    @bound_json_cache(SECONDS_IN.HOUR)
    def get_commodities(self, region, locale=None):
        if not locale:
            locale = self.get_default_locale(region)
        return self._api.wow.game_data.get_commodities(region, locale)


class API:
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
            self.wrapper = APIWrapper(client_id, client_secret, cache, *args, **kwargs)
        else:
            self.wrapper = wrapper

    def pull_connected_realms_ids(self, region: str):
        connected_realms = self.wrapper.get_connected_realms_index(region)
        for cr in connected_realms["connected_realms"]:
            ret = re.search(r"connected-realm/(\d+)", cr["href"])
            crid = ret.group(1)
            yield int(crid)

    def pull_connected_realm(self, region: str, crid: int):
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
        connected_realm = self.wrapper.get_connected_realm(region, crid)
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

    def pull_connected_realms(self, region: str):
        """

        >>> {
                # connected realms
                $crid: $crid_data,
                ...
            }
        """
        crids = self.pull_connected_realms_ids(region)
        ret = {}
        for crid in crids:
            connected_realm = self.pull_connected_realm(region, crid)
            ret[crid] = connected_realm

        return ret

    def pull_commodities(self, region: str):
        commodities = self.wrapper.get_commodities(region)
        return commodities

    def pull_auctions(self, region: str, crid: int):
        auctions = self.wrapper.get_auctions(region, crid)
        return auctions

    def get_timezone(self, region, connected_realm_id):
        """NOTE: CRs under same region may have different timezones!"""
        connected_realm = self._api.get_connected_realm(region, connected_realm_id)
        return connected_realm["realms"][0]["timezone"]
