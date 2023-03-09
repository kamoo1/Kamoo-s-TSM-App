import sys
import logging
import argparse

from ah import config
from ah.task_manager import TaskManager
from ah.api import API
from ah.cache import Cache
from ah.tsm_exporter import TSMExporter
from ah.storage import TextFile


def main(
    db_path: str = None,
    export_path: str = None,
    compress_db: bool = None,
    region: str = None,
    cache: Cache = None,
    api: API = None,
):
    if api is None:
        if cache is None:
            cache = Cache(config.TEMP_PATH, config.APP_NAME)
        api = API(
            config.BN_CLIENT_ID,
            config.BN_CLIENT_SECRET,
            cache,
        )
    task_manager = TaskManager(
        api,
        db_path,
        data_use_compression=compress_db,
        records_expires_in=config.MARKET_VALUE_RECORD_EXPIRES,
    )
    export_file = TextFile(export_path)
    exporter = TSMExporter()
    task_manager.update_dbs_under_region(
        region, exporter=exporter, export_file=export_file
    )


def parse_args(raw_args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_path", help="Path to database", default=config.TEMP_PATH, type=str
    )
    parser.add_argument(
        "--export_path",
        help="Export path",
        default=config.DEFAULT_EXPORT_PATH,
        type=str,
    )
    parser.add_argument(
        "--compress_db",
        help="Use compression for DB files",
        default=False,
        action="store_true",
    )
    parser.add_argument("region", help="Region to export", choices=config.REGIONS)
    args = parser.parse_args(raw_args)
    return args


if __name__ == "__main__":
    logging.basicConfig(level=config.LOGGING_LEVEL)
    args = parse_args(sys.argv[1:])
    main(**vars(args))
