"""hearthstone_game_data_api.py file."""
from ..api import Api


class HearthstoneGameDataApi(Api):
    """All Hearthstone Game Data API methods.

    Attributes:
        client_id: A string client id supplied by Blizzard.
        client_secret: A string client secret supplied by Blizzard.
    """

    def __init__(self, client_id, client_secret):
        """Init HearthstoneGameDataApi."""
        super().__init__(client_id, client_secret)

    # Cards

    def search_cards(self, region, locale, **query_params):
        """Return an up-to-date list of all cards matching the search criteria."""
        resource = "/hearthstone/cards"
        query_params.update({"locale": locale})
        return super().get_resource(resource, region, query_params)

    def get_card(self, region, locale, id_or_slug, game_mode="constructed"):
        """Return the card with an ID or slug that matches the one you specify."""
        resource = f"/hearthstone/cards/{id_or_slug}"
        query_params = {"locale": locale, "game_mode": game_mode}
        return super().get_resource(resource, region, query_params)

    # Card Backs

    def search_card_backs(self, region, locale, **query_params):
        """Return an up-to-date list of all card backs matching the search criteria."""
        resource = "/hearthstone/cardbacks"
        query_params.update({"locale": locale})
        return super().get_resource(resource, region, query_params)

    def get_card_back(self, region, locale, id_or_slug):
        """Return a specific card back by using card back ID or slug."""
        resource = f"/hearthstone/cardbacks/{id_or_slug}"
        query_params = {"locale": locale}
        return super().get_resource(resource, region, query_params)

    # Decks

    def get_deck(self, region, locale, **query_params):
        """Find a deck by list of cards or code, including the hero."""
        resource = "/hearthstone/deck"
        query_params = {"locale": locale}
        return super().get_resource(resource, region, query_params)

    # Metadata

    def get_metadata(self, region, locale):
        """Return information about the categorization of cards."""
        resource = "/hearthstone/metadata"
        query_params = {"locale": locale}
        return super().get_resource(resource, region, query_params)

    def get_metadata_type(self, region, locale, type_id):
        """Return information about just one type of metadata."""
        resource = f"/hearthstone/metadata/{type_id}"
        query_params = {"locale": locale}
        return super().get_resource(resource, region, query_params)
