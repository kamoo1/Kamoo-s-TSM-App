"""battlenet_oauth_api.py file."""
from ..api import Api


class BattlenetOauthApi(Api):
    """All Battle.net OAuth API methods.

    Attributes:
        client_id: A string client id supplied by Blizzard.
        client_secret: A string client secret supplied by Blizzard.
    """

    def __init__(self, client_id, client_secret):
        """Init BattlenetOauthApi."""
        super().__init__(client_id, client_secret)

    # User Authentication

    def get_user_info(self, region, access_token):
        """Return basic information about the user associated with the current bearer token."""
        resource = "/oauth/userinfo"
        query_params = {
            "access_token": access_token,
        }
        return super().get_oauth_resource(resource, region, query_params)
