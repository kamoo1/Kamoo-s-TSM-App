"""hearthstone_api.py file."""
from .hearthstone_game_data_api import HearthstoneGameDataApi


class HearthstoneApi:
    """Hearthstone API class.

    Attributes:
        client_id: A string client id supplied by Blizzard.
        client_secret: A string client secret supplied by Blizzard.
    """

    def __init__(self, client_id, client_secret):
        """Init HearthstoneApi."""
        self.game_data = HearthstoneGameDataApi(client_id, client_secret)
