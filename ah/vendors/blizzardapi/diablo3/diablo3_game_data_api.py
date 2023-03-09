"""diablo3_game_data_api.py file."""
from ..api import Api


class Diablo3GameDataApi(Api):
    """All Diablo 3 Game Data API methods.

    Attributes:
        client_id: A string client id supplied by Blizzard.
        client_secret: A string client secret supplied by Blizzard.
    """

    def __init__(self, client_id, client_secret):
        """Init Diablo3GameDataApi."""
        super().__init__(client_id, client_secret)

    # D3

    def get_season_index(self, region):
        """Return an index of available seasons."""
        resource = "/data/d3/season/"
        return super().get_resource(resource, region)

    def get_season(self, region, season_id):
        """Return a leaderboard list for the specified season."""
        resource = f"/data/d3/season/{season_id}"
        return super().get_resource(resource, region)

    def get_season_leaderboard(self, region, season_id, leaderboard_id):
        """Return a the specified leaderboard for the specified season."""
        resource = f"/data/d3/season/{season_id}/leaderboard/{leaderboard_id}"
        return super().get_resource(resource, region)

    def get_era_index(self, region):
        """Return an index of available eras."""
        resource = "/data/d3/era/"
        return super().get_resource(resource, region)

    def get_era(self, region, era_id):
        """Return a leaderboard list for a particular era."""
        resource = f"/data/d3/era/{era_id}"
        return super().get_resource(resource, region)

    def get_era_leaderboard(self, region, era_id, leaderboard_id):
        """Return the specified leaderboard for the specified era."""
        resource = f"/data/d3/era/{era_id}/leaderboard/{leaderboard_id}"
        return super().get_resource(resource, region)
