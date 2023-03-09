"""wow_api.py file."""
from .wow_game_data_api import WowGameDataApi
from .wow_profile_api import WowProfileApi


class WowApi:
    """Wow API class.

    Attributes:
        client_id: A string client id supplied by Blizzard.
        client_secret: A string client secret supplied by Blizzard.
    """

    def __init__(self, client_id, client_secret):
        """Init WowApi."""
        self.game_data = WowGameDataApi(client_id, client_secret)
        self.profile = WowProfileApi(client_id, client_secret)
