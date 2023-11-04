from unittest import TestCase
from unittest.mock import patch, Mock
from tempfile import TemporaryDirectory
import re
import os
import requests
from urllib import parse

from ah.cache import Cache
from ah.api import GHAPI, UpdateEnum


class MockResponse(Mock):
    links = requests.Response.links

    def __init__(self, content, status_code=200, headers=None) -> None:
        super().__init__()
        self.headers = headers or {}
        self.content = content
        self.status_code = status_code

    def json(self):
        return self.content


class MockSession(Mock):
    MATCH_TAGS = re.compile(r"^https://api.github.com/repos/\w+/\w+/tags")
    MATCH_RELEASES_TAGS = re.compile(
        r"^https://api.github.com/repos/\w+/\w+/releases/tags/\w+"
    )
    MATCH_RELEASES_ASSETS = re.compile(
        r"^https://api.github.com/repos/\w+/\w+/releases/\d+/assets"
    )
    MATCH_CDN = re.compile(r"^https://example.com/cdn")
    MATCH_PAGINATION = re.compile(r"^https://example.com/pagination")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def request(self, method, url, **kwargs):
        if method == "get":
            return self.get(url, **kwargs)

        else:
            raise NotImplementedError

    def get(self, url: str, **kwargs):
        if self.MATCH_TAGS.match(url):
            return MockResponse(
                [
                    {
                        "name": "v1.1.0",
                    },
                    {
                        "name": "v1.2.0",
                    },
                    {
                        "name": "v1.3.0",
                    },
                ]
            )
        elif self.MATCH_RELEASES_TAGS.match(url):
            return MockResponse(
                {
                    "id": 123,
                }
            )
        elif self.MATCH_RELEASES_ASSETS.match(url):
            return MockResponse(
                [
                    {
                        "name": "archive.zip",
                        "browser_download_url": "https://example.com/cdn/archive.zip",
                    },
                ]
            )
        elif self.MATCH_CDN.match(url):
            return MockResponse(b"content")
        elif self.MATCH_PAGINATION.match(url):
            # get url param `page` from url
            parse_ = parse.urlparse(url)
            query = parse.parse_qs(parse_.query)
            page = int(query["page"][0]) if "page" in query else 1

            return MockResponse(
                [f"page-{page}-item-{i}" for i in range(10)],
                headers={
                    "link": f"<{parse_.scheme}://{parse_.netloc}{parse_.path}?"
                    f'page={page + 1}>; rel="next"'
                }
                if page < 10
                else {},
            )


class TestGHApi(TestCase):
    def setUp(self) -> None:
        self.patcher = patch("requests.Session", MockSession)
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_update(self):
        temp = TemporaryDirectory()
        with temp:
            cache_path = os.path.join(temp.name, "cache")
            cache = Cache(cache_path)
            api = GHAPI(cache)

            # optional update
            stat, latest_ver = api.check_update("user", "repo", current_ver="v1.1.0")
            self.assertEqual(stat, UpdateEnum.OPTIONAL)
            self.assertEqual(latest_ver, "1.3.0")

            # no update
            stat, latest_ver = api.check_update("user", "repo", current_ver="v1.3.0")
            self.assertEqual(stat, UpdateEnum.NONE)
            self.assertEqual(latest_ver, "1.3.0")

            # required update
            stat, latest_ver = api.check_update("user", "repo", current_ver="v0.3.0")
            self.assertEqual(stat, UpdateEnum.REQUIRED)
            self.assertEqual(latest_ver, "1.3.0")

            content = api.get_build_release("user", "repo", "v1.3.0")
            self.assertEqual(content, b"content")

    def test_pagination(self):
        temp = TemporaryDirectory()
        with temp:
            cache_path = os.path.join(temp.name, "cache")
            cache = Cache(cache_path)
            api = GHAPI(cache)
            for i, resp in enumerate(api.paginated("https://example.com/pagination")):
                self.assertEqual(resp.status_code, 200)
                expected = [f"page-{i + 1}-item-{j}" for j in range(10)]
                self.assertEqual(resp.json(), expected)

            self.assertEqual(i, 9)
