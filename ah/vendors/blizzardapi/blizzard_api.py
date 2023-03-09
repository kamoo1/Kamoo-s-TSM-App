"""blizzard_api.py file."""
from .battlenet.battlenet_api import BattlenetApi
from .diablo3.diablo3_api import Diablo3Api
from .hearthstone.hearthstone_api import HearthstoneApi
from .wow.wow_api import WowApi


class BlizzardApi:
    """Blizzard API class.

    Attributes:
        client_id: A string client id supplied by Blizzard.
        client_secret: A string client secret supplied by Blizzard.
    """

    def __init__(self, client_id, client_secret):
        """Init BlizzardApi."""
        self.battlenet = BattlenetApi(client_id, client_secret)
        self.diablo3 = Diablo3Api(client_id, client_secret)
        self.hearthstone = HearthstoneApi(client_id, client_secret)
        self.wow = WowApi(client_id, client_secret)
