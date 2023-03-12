"""this is a file-based key-value store, expriation is calculated by the file's last
modified time.
"""

import os
import time
import pickle
import hashlib
from typing import Callable, Any, Union
from logging import getLogger
from functools import wraps

from ah.fs import ensure_path, remove_path


class Cache:
    def __init__(self, cache_path: str) -> None:

        # get temp path of the system,
        # (e.g. /tmp on linux, C:\Users\username\AppData\Local\Temp on windows)
        self._logger = getLogger(__name__)
        self.cache_path = cache_path
        ensure_path(self.cache_path)

    def _get_path(self, key: str) -> str:
        """Get the path of a key."""
        return os.path.join(self.cache_path, key)

    @classmethod
    def _get_key_str(cls, key: Any) -> str:
        """Get the string representation of a key."""
        key_data = pickle.dumps(key)
        return hashlib.sha256(key_data).hexdigest()

    def get(
        self, key: Any, default: Any = None, expires: Union[int, float] = -1
    ) -> Any:
        """Get a value from the cache.
        when expires >= 0, return cache if exists and not expired (current time minus
        cache modification time), otherwise return default.
        when expires < 0, return cache if exists, otherwise return default.

        """
        key = self._get_key_str(key)

        path = self._get_path(key)
        if not os.path.exists(path):
            self._logger.debug(f"cache get: {key} not found")
            return default

        # check expiration
        modtime = os.path.getmtime(path)
        if expires >= 0 and time.time() - modtime > expires:
            self._logger.debug(f"cache get: {key} expired")
            return default

        with open(path, "rb") as file:
            self._logger.debug(f"cache get: {key} hit")
            data = file.read()
            return pickle.loads(data)

    def set(self, key: Any, value: Any) -> None:
        """Set a value in the cache."""
        key = self._get_key_str(key)
        path = self._get_path(key)
        data = pickle.dumps(value)
        with open(path, "wb") as file:
            file.write(data)
        self._logger.debug(f"cache set: {key}")

    def purge(self) -> None:
        """Purge the cache by removing files under cache dir."""
        remove_path(self.cache_path)


class BoundCacheMixin:
    """A mixin to bind a cache instance to a class."""

    def __init__(self, cache: Cache, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if hasattr(self, "_cache"):
            raise ValueError("attribute _cache is already defined")

        self._cache = cache


def bound_cache(expires: int) -> Callable:
    """a decorator to cache the result of a function which returns a json-like object,
    key is the hash of the function name and it's arguments.
    """

    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        def inner(that: BoundCacheMixin, *args, **kwargs) -> Any:
            # hash function should be SHA-256
            key = {"fname": func.__name__, "args": args, "kwargs": kwargs}
            if hasattr(that, "_cache"):
                cache = that._cache.get(key, expires=expires)
                if cache is None:
                    value = func(that, *args, **kwargs)
                    that._cache.set(key, value)
                else:
                    value = cache

            else:
                value = func(that, *args, **kwargs)

            return value

        return inner

    return wrapper
