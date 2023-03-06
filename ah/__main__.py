import json
import time
import os
import logging

from ah import config
from ah.task_manager import TaskManager
from ah.cache import Cache
from ah.api import API
from ah.fs import get_temp_path
from ah.tsm_exporter import TSMExporter
from ah.storage import TextFile


def pprint(obj):
    print(json.dumps(obj, indent=4, ensure_ascii=False))


def test():
    data_base_path = get_temp_path()
    cache = Cache(data_base_path, config.APP_NAME)
    logging.basicConfig(level=logging.DEBUG)
    api = API(config.BN_CLIENT_ID, config.BN_CLIENT_SECRET, cache)
    # ah = TaskManager(api)
    # # connected_realms = ah.get_connected_realms("tw")
    # # pprint(connected_realms)
    # # auctions = ah.get_auctions("tw", 980)
    # # pprint(auctions)
    # resp = ah.request_auctions("tw", 980)
    # inc = ah.resp_to_increments(resp, time.time())
    # print(inc)
    # resp = ah._pull_connected_realms("tw")
    # pprint(resp)

    # resp = ah.request_commodities("tw")
    # timestamp = time.time()
    # increments = ah.resp_to_increments(resp, timestamp)
    # ah.update_commodities_market_value_file("tw", increments)

    # pprint(commodities)
    # z = ah._get_timezone("us")
    # print(z)
    # comm_market_values = ah.get_commodities_mv_increment("tw")
    # print(comm_market_values[197788])
    # for i in range(30 * 6):
    #     print(i)
    #     ah.update_commodities_mv("us")

    data_path = os.path.join([config.DATA_BASE_PATH, config.APP_NAME])
    task_manager = TaskManager(
        api,
        data_path,
        data_use_compression=True,
        records_expires_in=config.MARKET_VALUE_RECORD_EXPIRES,
    )
    # TODO: change path here
    export_file = TextFile("./export.txt")
    exporter = TSMExporter()
    task_manager.update_dbs_under_region(
        "tw", exporter=exporter, export_file=export_file
    )


if __name__ == "__main__":
    test()
