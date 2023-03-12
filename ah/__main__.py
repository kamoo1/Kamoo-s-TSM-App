import os
import sys
import logging
import argparse

from ah import config
from ah.task_manager import TaskManager
from ah.api import BNAPI
from ah.db import AuctionDB
from ah.cache import Cache
from ah.models import Region


def main(
    db_path: str = None,
    compress_db: bool = None,
    region: Region = None,
    cache: Cache = None,
    bn_api: BNAPI = None,
):
    if bn_api is None:
        if cache is None:
            cache_path = os.path.join(config.TEMP_PATH, config.APP_NAME + "_cache")
            cache = Cache(cache_path)
        bn_api = BNAPI(
            config.BN_CLIENT_ID,
            config.BN_CLIENT_SECRET,
            cache,
        )
    db = AuctionDB(db_path, config.MARKET_VALUE_RECORD_EXPIRES, compress_db)
    task_manager = TaskManager(bn_api, db)
    task_manager.update_dbs_under_region(region)


def parse_args(raw_args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_path", help="Path to database", default=config.TEMP_PATH, type=str
    )
    parser.add_argument(
        "--compress_db",
        help="Use compression for DB files",
        default=False,
        action="store_true",
    )
    parser.add_argument("region", help="Region to export", type=Region)
    args = parser.parse_args(raw_args)
    return args


if __name__ == "__main__":
    logging.basicConfig(level=config.LOGGING_LEVEL)
    args = parse_args(sys.argv[1:])
    main(**vars(args))
