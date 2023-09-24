import os
import io
from unittest import mock
import hashlib
from unittest import TestCase
from tempfile import TemporaryDirectory

from ah.patcher import (
    main,
    PatcherHashError,
)


class TestPatcher(TestCase):
    DATA_SRC = "a\nb\nc\n"
    DATA_DST = "bb\nc\nd\n"
    DATA_DIFF = "@@ -1,6 +1,7 @@\n-a%0A\n+b\n b%0Ac%0A\n+d%0A\n"
    SRC_DIGEST = hashlib.sha256(DATA_SRC.encode()).hexdigest()

    @classmethod
    def mock_files(
        cls,
        base_path: str,
        data_src: str = None,
        data_dst: str = None,
        data_diff: str = None,
    ):
        """make files under `base_path` with the given data."""

        names = ["src", "dst", "diff"]
        ret = []
        for name, data in zip(
            names,
            [data_src, data_dst, data_diff],
        ):
            file_path = os.path.join(base_path, name)
            if data:
                with open(file_path, "w", newline="\n") as f:
                    f.write(data)

            ret.append(file_path)

        return ret

    def test_all(self):
        data_src = self.DATA_SRC
        data_dst = self.DATA_DST
        data_diff = self.DATA_DIFF
        hash_src = self.SRC_DIGEST

        """
        Diff
        """
        temp = TemporaryDirectory()
        with temp:
            path_src, path_dst, path_diff = self.mock_files(
                base_path=temp.name,
                data_src=data_src,
                data_dst=data_dst,
                data_diff=None,
            )
            args = [
                "diff",
                path_src,
                path_dst,
                "--out",
                path_diff,
            ]
            main(args)

            # assert the diff
            with open(path_diff, "r", newline="\n") as f:
                actual = f.read()
                self.assertEqual(actual, data_diff)

        """
        Hash
        """
        temp = TemporaryDirectory()
        with temp:
            path_src, path_dst, path_diff = self.mock_files(
                base_path=temp.name,
                data_src=data_src,
                data_dst=None,
                data_diff=None,
            )
            args = [
                "hash",
                path_src,
            ]
            with mock.patch("sys.stdout", new=io.StringIO()) as mock_stdout:
                main(args)
                actual = mock_stdout.getvalue()
                self.assertEqual(actual, hash_src + "\n")

        """
        Patching & src hash check
        """
        temp = TemporaryDirectory()
        with temp:
            path_src, path_dst, path_diff = self.mock_files(
                base_path=temp.name,
                data_src=data_src,
                data_dst=None,
                data_diff=data_diff,
            )
            args = [
                "patch",
                path_src,
                path_diff,
                "--src_digest",
                hash_src,
                "--out",
                path_dst,
            ]

            # assert patch result
            main(args)
            with open(path_dst, "r", newline="\n") as f:
                actual = f.read()
                self.assertEqual(actual, data_dst)

            # should be idempotent
            main(args)
            with open(path_dst, "r", newline="\n") as f:
                actual = f.read()
                self.assertEqual(actual, data_dst)

        """
        In place patching & src hash check
        """
        temp = TemporaryDirectory()
        with temp:
            path_src, path_dst, path_diff = self.mock_files(
                base_path=temp.name,
                data_src=data_src,
                data_dst=None,
                data_diff=data_diff,
            )
            args = [
                "patch",
                path_src,
                path_diff,
                "--in_place",
                "--src_digest",
                hash_src,
            ]
            main(args)

            # we already patched the src file,
            # so the hash should not match org this time.
            self.assertRaises(
                PatcherHashError,
                main,
                args,
            )

            # assert patch result
            with open(path_src, "r", newline="\n") as f:
                actual = f.read()
                self.assertEqual(actual, data_dst)
