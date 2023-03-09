from ah.vendors.blizzardapi import BlizzardApi
from ah.cache import bound_json_cache, BoundCacheMixin, Cache
from ah.defs import SECONDS_IN


class API(BoundCacheMixin):
    def __init__(self, client_id, client_secret, cache: Cache, *args, **kwargs) -> None:
        super().__init__(*args, cache=cache, **kwargs)
        self._locale = "en_US"
        self._api = BlizzardApi(client_id, client_secret)

    @bound_json_cache(SECONDS_IN.WEEK)
    def get_connected_realms_index(self, region):
        return self._api.wow.game_data.get_connected_realms_index(region, self._locale)

    @bound_json_cache(SECONDS_IN.WEEK)
    def get_connected_realm(self, region, connected_realm_id):
        return self._api.wow.game_data.get_connected_realm(
            region, self._locale, connected_realm_id
        )

    @bound_json_cache(SECONDS_IN.HOUR)
    def get_auctions(self, region, connected_realm_id):
        return self._api.wow.game_data.get_auctions(
            region, self._locale, connected_realm_id
        )

    @bound_json_cache(SECONDS_IN.HOUR)
    def get_commodities(self, region):
        return self._api.wow.game_data.get_commodities(region, self._locale)
