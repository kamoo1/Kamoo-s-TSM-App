from unittest import TestCase
from unittest.mock import patch, Mock
from tempfile import TemporaryDirectory
import re
import os

from ah.cache import Cache
from ah.api import GHAPI, UpdateEnum


class MockResponse(Mock):
    def __init__(self, content, status_code=200) -> None:
        super().__init__()
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
    MATCH_CDN_COM = re.compile(r"^https://cdn.com/")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

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
                        "browser_download_url": "https://cdn.com/archive.zip",
                    },
                ]
            )
        elif self.MATCH_CDN_COM.match(url):
            return MockResponse(b"content")


class TestGHApi(TestCase):
    def setUp(self) -> None:
        print("setup")
        self.patcher = patch("requests.Session", MockSession)
        self.patcher.start()

    def tearDown(self) -> None:
        print("teardown")
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
            self.assertEqual(latest_ver, None)

            # required update
            stat, latest_ver = api.check_update("user", "repo", current_ver="v0.3.0")
            self.assertEqual(stat, UpdateEnum.REQUIRED)
            self.assertEqual(latest_ver, "1.3.0")

            content = api.get_build_release("user", "repo", "v1.3.0")
            self.assertEqual(content, b"content")
