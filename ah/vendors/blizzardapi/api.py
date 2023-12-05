"""api.py file."""
import requests
from requests.adapters import HTTPAdapter, Retry

from ah import config


class Api:
    """Base API class.

    Attributes:
        _client_id: A string client id supplied by Blizzard.
        _client_secret: A string client secret supplied by Blizzard.
        _access_token: A string access token that is used to access Blizzard's API.
        _api_url: A string url used to call the API endpoints.
        _api_url_cn: A string url used to call the china API endpoints.
        _oauth_url: A string url used to call the OAuth API endpoints.
        _oauth_url_cn: A string url used to call the china OAuth API endpoints.
        _session: An open requests.Session instance.
    """

    def __init__(self, client_id, client_secret):
        """Init Api."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = None

        self._api_url = "https://{0}.api.blizzard.com{1}"
        self._api_url_cn = "https://gateway.battlenet.com.cn{0}"

        # self._oauth_url = "https://{0}.battle.net{1}"
        # self._oauth_url_cn = "https://www.battlenet.com.cn{0}"
        self._oauth_url = "https://oauth.battle.net{0}"
        self._oauth_url_cn = "https://oauth.battlenet.com.cn{0}"

        self._session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=1, status_forcelist=[429]
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retries))
        self._session.mount("http://", HTTPAdapter(max_retries=retries))

    def _get_client_token(self, region):
        """Fetch an access token based on client id and client secret credentials.

        Args:
            region:
                A string containing a region.
        """
        # url = self._format_oauth_url("/oauth/token", region)
        url = self._format_oauth_url("/token", region)
        query_params = {"grant_type": "client_credentials"}

        response = self._session.post(
            url,
            params=query_params,
            auth=(self._client_id, self._client_secret),
        )
        return self._response_handler(response)

    def _response_handler(self, response):
        """Handle the response."""
        response.raise_for_status()
        resp = response.json()
        return resp

    def _request_handler(self, url, region, query_params):
        """Handle the request."""
        if self._access_token is None:
            json = self._get_client_token(region)
            self._access_token = json["access_token"]

        if query_params.get("access_token") is None:
            query_params["access_token"] = self._access_token

        response = self._session.get(url, params=query_params, verify=config.VERIFY_SSL)

        return self._response_handler(response)

    def _format_api_url(self, resource, region):
        """Format the API url into a usable url."""
        if region == "cn":
            url = self._api_url_cn.format(resource)
        else:
            url = self._api_url.format(region, resource)

        return url

    def get_resource(self, resource, region, query_params={}):
        """Direction handler for when fetching resources."""
        url = self._format_api_url(resource, region)
        return self._request_handler(url, region, query_params)

    def _format_oauth_url(self, resource, region):
        """Format the oauth url into a usable url."""
        if region == "cn":
            url = self._oauth_url_cn.format(resource)
        else:
            # url = self._oauth_url.format(region, resource)
            url = self._oauth_url.format(resource)

        return url

    def get_oauth_resource(self, resource, region, query_params={}):
        """Direction handler for when fetching oauth resources."""
        url = self._format_oauth_url(resource, region)
        return self._request_handler(url, region, query_params)
