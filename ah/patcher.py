import io
import os
import sys
import json
import hashlib
import argparse
from typing import Callable, List, Dict, Any
import logging

from diff_match_patch import diff_match_patch

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

_logger = logging.getLogger(__name__)


class PatcherBaseError(Exception):
    pass


class PatcherHashError(PatcherBaseError):
    pass


class PatcherFileError(PatcherBaseError):
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


def get_hash(f: io.TextIOWrapper) -> str:
    hash_str = hashlib.sha256()
    hash_str.update(f.read().encode("utf-8"))
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
    src_digest: io.TextIOWrapper | None,
) -> None:
    if src_digest is not None:
        digest = src_digest.read()
        digest = digest.strip()
        if digest != get_hash(src):
            raise PatcherHashError("Source file hash does not match.")
        src.seek(0)

    dst_data = get_dst(src, diff)
    if in_place:
        out = src
        out.seek(0)
        out.truncate()

    out.write(dst_data)


def hash_(*, file: io.TextIOWrapper, out: io.TextIOWrapper) -> None:
    h = get_hash(file)
    out.write(h + "\n")


def batch_patch(jobs_json: io.TextIOWrapper) -> None:
    try:
        args_list = json.load(jobs_json)

    except Exception:
        _logger.fatal(f"batch_patch: failed to load jobs from {jobs_json.name!r}")
        raise

    finally:
        jobs_json.close()

    # TODO: add os support other than Windows
    warcraft_base = TSMExporter.find_warcraft_base()
    if not warcraft_base:
        raise PatcherFileError("Failed to find warcraft base.")

    vars = {"warcraft_base": warcraft_base}
    n = len(args_list)
    for i, args in enumerate(args_list):
        try:
            args_ = [arg.format(**vars) for arg in args]
            args_.insert(0, "patch")
            main(args_)

        except Exception:
            _logger.warning(f"batch_patch: failed to run job {i+1}/{n}")
            _logger.debug(f"batch_patch: {args_=!r}", exc_info=True)

        else:
            _logger.info(f"batch_patch: job {i+1}/{n} done")


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
        type=file_type("r"),
        help="a file containing sha256 digest of source file, "
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
        "--out",
        type=file_type("w"),
        default=sys.stdout,
        help="output file, default: stdout",
    )
    parser_hash.add_argument(
        "file",
        type=file_type("r"),
        help="file to get the digest of",
    )
    parser_batch_patch = sub_parsers.add_parser(
        "batch_patch",
        help="batch patch files.",
    )
    parser_batch_patch.set_defaults(func=batch_patch)
    parser_batch_patch.add_argument(
        "jobs_json",
        type=file_type("r"),
        help="a json file containing a list of jobs, "
        "each job is a list of arguments for patch function. "
        'for example: [["--in_place", "path/src", "path/diff"], ...]',
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
        "src_digest",
    ]
    kwargs = parse_args(args)
    func = kwargs.pop("func")
    # stds might be `None` after `Pyinstaller` packaging
    stds = filter(None, (sys.stdin, sys.stdout, sys.stderr))
    std_names = {std.name for std in stds}

    try:
        func(**kwargs)
    finally:
        for key in need_close:
            f = kwargs.get(key)
            if isinstance(f, io.TextIOWrapper) and f.name not in std_names:
                f.close()


if __name__ == "__main__":
    main()
