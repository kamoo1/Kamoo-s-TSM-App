"""this is a file-based key-value store, expriation is calculated by the file's last
modified time.
"""

import os
import time
import json
import pickle
import hashlib
from typing import Callable
from logging import getLogger

from ah.fs import ensure_path, remove_path


class Cache:
    def __init__(self, base_path: str, app_name: str):

        # get temp path of the system,
        # (e.g. /tmp on linux, C:\Users\username\AppData\Local\Temp on windows)
        self._logger = getLogger(__name__)

        folder_name = "{}.json_cache".format(app_name)
        self.base_path = os.path.join(base_path, folder_name)
        ensure_path(self.base_path)

    def _get_path(self, key):
        """Get the path of a key."""
        return os.path.join(self.base_path, key)

    def get(self, key, default=None, expires=-1):
        """Get a value from the cache.
        when expires >= 0, return cache if exists and not expired (current time minus
        cache modification time), otherwise return default.
        when expires < 0, return cache if exists, otherwise return default.

        """

        if not isinstance(expires, int):
            raise TypeError("expires must be an integer")

        path = self._get_path(key)
        if not os.path.exists(path):
            self._logger.debug(f"cache get: {key} not found")
            return default

        # check expiration
        modtime = os.path.getmtime(path)
        if time.time() - modtime > expires:
            self._logger.debug(f"cache get: {key} expired")
            return default

        with open(path, "rb") as file:
            self._logger.debug(f"cache get: {key} hit")
            return file.read()

    def set(self, key, value):
        """Set a value in the cache."""
        path = self._get_path(key)
        with open(path, "wb") as file:
            file.write(value)
        self._logger.debug(f"cache set: {key}")

    def purge(self):
        """Purge the cache by removing files under cache dir."""
        remove_path(self.base_path)


class BoundCacheMixin:
    """A mixin to bind a cache instance to a class."""

    def __init__(self, cache: Cache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "_cache"):
            raise ValueError("attribute _cache is already defined")

        self._cache = cache


def bound_json_cache(expires: int):
    """a decorator to cache the result of a function which returns a json-like object,
    key is the hash of the function name and it's arguments.
    """

    def wrapper(func: Callable):
        def inner(that: BoundCacheMixin, *args, **kwargs):
            # hash function should be SHA-256
            obj = pickle.dumps({"fname": func.__name__, "args": args, "kwargs": kwargs})
            key = hashlib.sha256(obj).hexdigest()
            if hasattr(that, "_cache"):
                cache = that._cache.get(key, expires=expires)
                if cache is None:
                    value = func(that, *args, **kwargs)
                    that._cache.set(key, json.dumps(value).encode())
                else:
                    value = json.loads(cache.decode())

            else:
                value = func(that, *args, **kwargs)

            return value

        return inner

    return wrapper
