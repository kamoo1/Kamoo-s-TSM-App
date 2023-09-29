import io
import os
import sys
import hashlib
import argparse
from typing import Callable, List, Dict, Any
import logging

from diff_match_patch import diff_match_patch

from ah.models.blizzard import GameVersionEnum
from ah.tsm_exporter import TSMExporter

__all__ = (
    "PatcherBaseError",
    "PatcherHashError",
    "diff",
    "patch",
    "get_dst",
    "get_diff",
    "get_hash",
)

PATH_WOW_TO_TSM_LRI = [
    "Interface",
    "AddOns",
    "TradeSkillMaster",
    "External",
    "EmbeddedLibs",
    "LibRealmInfo",
    "LibRealmInfo.lua",
]

_logger = logging.getLogger(__name__)


class PatcherBaseError(Exception):
    pass


class PatcherHashError(PatcherBaseError):
    pass


def get_dst(
    src_file: io.TextIOWrapper,
    diff_file: io.TextIOWrapper,
) -> str:
    """Make the modified file from the original and diff files."""
    data_src = src_file.read()
    data_diff = diff_file.read()

    dmp = diff_match_patch()
    patch = dmp.patch_fromText(data_diff)
    dst, _ = dmp.patch_apply(patch, data_src)
    return dst


def get_diff(
    src_file: io.TextIOWrapper,
    dst_file: io.TextIOWrapper,
) -> str:
    """Make the diff file from the original and modified files."""
    data_src = src_file.read()
    data_dst = dst_file.read()

    dmp = diff_match_patch()
    patch = dmp.patch_make(data_src, data_dst)
    text = dmp.patch_toText(patch)
    return text


def get_hash(f: io.TextIOWrapper, read_rest: bool = False) -> str:
    hash_str = hashlib.sha256()
    hash_str.update(f.read().encode("utf-8"))
    if read_rest:
        f.seek(0)

    return hash_str.hexdigest()


def diff(
    *,
    src: io.TextIOWrapper,
    dst: io.TextIOWrapper,
    out: io.TextIOWrapper,
) -> None:
    out.write(get_diff(src, dst))


def patch(
    *,
    src: io.TextIOWrapper,
    diff: io.TextIOWrapper,
    out: io.TextIOWrapper,
    in_place: bool,
    src_digest: str | None,
) -> None:
    if src_digest is not None and src_digest != get_hash(src, read_rest=True):
        raise PatcherHashError("Source file hash does not match.")

    dst_data = get_dst(src, diff)
    if in_place:
        out = src
        out.seek(0)
        out.truncate()

    out.write(dst_data)


def hash_(*, file: io.TextIOWrapper) -> None:
    sys.stdout.write(get_hash(file) + "\n")


def patch_tsm(
    warcraft_base: str = None,
    *,
    src_digest: str,
    diff: io.TextIOWrapper,
) -> None:
    """patch `LibRealmInfo.lua` with recently added realms.
    many newly added kr, tw realms are not listed in existing
    `LibRealmInfo.lua`, sometimes this will cause TSM assign
    them a wrong the region.

    f_diff: diff file
    f_src_digest: source (original) file hash

    """
    warcraft_base = warcraft_base or TSMExporter.find_warcraft_base()
    version_paths = (version.get_version_folder_name() for version in GameVersionEnum)
    src_paths = (
        os.path.join(
            warcraft_base,
            version,
            *PATH_WOW_TO_TSM_LRI,
        )
        for version in version_paths
    )

    for src in src_paths:
        if not os.path.isfile(src):
            continue
        with open(src, "r+", encoding="utf-8") as f:
            try:
                diff.seek(0)
                patch(
                    src=f,
                    diff=diff,
                    out=None,
                    in_place=True,
                    src_digest=src_digest,
                )
            except PatcherHashError:
                _logger.warning(
                    f"Failed to patch {src!r}, "
                    f"file may have been patched already, "
                    f"or it's been updated by TSM."
                )
            else:
                _logger.info(f"Patched {src!r}.")


def file_type(mode="r") -> Callable:
    def _file_type(path: str) -> io.TextIOWrapper:
        path = os.path.normpath(path)
        return open(path, mode, encoding="utf-8")

    return _file_type


def parse_args(args: List[str]) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="A simple text file patcher.")
    sub_parsers = parser.add_subparsers(help="functions")
    parser_diff = sub_parsers.add_parser(
        "diff",
        help="make diff file.",
    )
    parser_diff.set_defaults(func=diff)
    parser_diff.add_argument(
        "--out",
        type=file_type(mode="w"),
        default=sys.stdout,
        help="output file, default: stdout. ",
    )
    parser_diff.add_argument(
        "src",
        type=file_type("r"),
        help="source file",
    )
    parser_diff.add_argument(
        "dst",
        type=file_type("r"),
        help="destination file",
    )
    parser_patch = sub_parsers.add_parser(
        "patch",
        help="make destination file from source and diff files.",
    )
    parser_patch.set_defaults(func=patch)
    parser_patch.add_argument(
        "--out",
        type=file_type("w"),
        default=sys.stdout,
        help="output file, default: stdout",
    )
    parser_patch.add_argument(
        "--in_place",
        action="store_true",
        help="modify source file in place, takes precedence over --out, "
        "default: stdout",
    )
    parser_patch.add_argument(
        "--src_digest",
        type=str,
        help="sha256 digest of source file, "
        "if given, raises error if the digest does not match. "
        "always use digest generated from this program, because "
        "while reading, it standardizes all newlines to \\n, "
        "potentially changing the digest. default: None",
    )
    parser_patch.add_argument(
        "src",
        type=file_type("r+"),
        help="source file",
    )
    parser_patch.add_argument(
        "diff",
        type=file_type("r"),
        help="diff file",
    )
    parser_hash = sub_parsers.add_parser(
        "hash",
        help="get sha256 digest of the file.",
    )
    parser_hash.set_defaults(func=hash_)
    parser_hash.add_argument(
        "file",
        type=file_type("r"),
        help="file to get the digest of",
    )
    parser_patch_tsm = sub_parsers.add_parser(
        "patch_tsm",
        help="patch `LibRealmInfo.lua` for all versions of warcraft "
        "with recently added realms.",
    )
    parser_patch_tsm.set_defaults(func=patch_tsm)
    parser_patch_tsm.add_argument(
        "src_digest",
        type=str,
        help="sha256 digest of source file",
    )
    parser_patch_tsm.add_argument(
        "diff",
        type=file_type("r"),
        help="diff file",
    )
    parsed = parser.parse_args(args)
    if not hasattr(parsed, "func"):
        parser.print_help()
        sys.exit(1)

    return vars(parsed)


def main(args: List[str] = sys.argv[1:]):
    need_close = [
        "src",
        "dst",
        "diff",
        "out",
        "file",
    ]
    kwargs = parse_args(args)
    func = kwargs.pop("func")

    try:
        func(**kwargs)
    finally:
        for key in need_close:
            if isinstance(kwargs.get(key), io.TextIOWrapper):
                kwargs[key].close()


if __name__ == "__main__":
    main()
