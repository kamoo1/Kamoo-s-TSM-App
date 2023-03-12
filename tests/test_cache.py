from unittest import TestCase, mock
import tempfile

from ah.cache import Cache, bound_cache, BoundCacheMixin


class Foo(BoundCacheMixin):
    def __init__(self, cache: Cache):
        super().__init__(cache)

    @bound_cache(expires=10)
    def foo(self):
        if not hasattr(self, "count"):
            self.count = 0
        self.count += 1
        return self.count


class TestCache(TestCase):
    def test_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Cache(tmpdir)
            cache.set("key", "value")
            self.assertEqual(cache.get("key"), "value")
            self.assertEqual(cache.get("key", expires=-1), "value")

            with mock.patch("os.path.getmtime", return_value=100), mock.patch(
                "time.time", return_value=110
            ):
                self.assertEqual(cache.get("key", expires=9), None)
                self.assertEqual(cache.get("key", default=..., expires=9), ...)
                self.assertEqual(cache.get("key", expires=10), "value")
                self.assertEqual(cache.get("key", expires=11), "value")

            cache.purge()

    def test_bound_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = Cache(tmpdir)
            foo = Foo(cache)
            self.assertEqual(foo.foo(), 1)
            self.assertEqual(foo.foo(), 1)

            with mock.patch("os.path.getmtime", return_value=100), mock.patch(
                "time.time", return_value=110
            ):
                self.assertEqual(foo.foo(), 1)
                self.assertEqual(foo.foo(), 1)

            with mock.patch("os.path.getmtime", return_value=100), mock.patch(
                "time.time", return_value=111
            ):
                self.assertEqual(foo.foo(), 2)
                self.assertEqual(foo.foo(), 3)

            with mock.patch("os.path.getmtime", return_value=100), mock.patch(
                "time.time", return_value=110
            ):
                self.assertEqual(foo.foo(), 3)
                self.assertEqual(foo.foo(), 3)

            cache.purge()
