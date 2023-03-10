from ah.vendors.blizzardapi import BlizzardApi
from ah.cache import bound_json_cache, BoundCacheMixin, Cache
from ah.defs import SECONDS_IN


class API(BoundCacheMixin):
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
