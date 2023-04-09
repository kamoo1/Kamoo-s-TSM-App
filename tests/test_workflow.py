from unittest import TestCase, mock
from random import shuffle, randint
from tempfile import TemporaryDirectory
import os

from ah.updater import Updater
from ah.models import (
    CommoditiesResponse,
    MapItemStringMarketValueRecords,
    MapItemStringMarketValueRecord,
    ItemString,
    ItemStringTypeEnum,
    GameVersionEnum,
    Namespace,
    NameSpaceCategoriesEnum,
    DBTypeEnum,
    RegionEnum,
)
from ah.api import BNAPI
from ah.db import AuctionDB
from ah.updater import main, parse_args


class DummyAPIWrapper:
    def get_connected_realms_index(self, region):
        return {
            "connected_realms": [
                {
                    "href": (
                        "https://us.api.blizzard.com/data/wow/"
                        "connected-realm/1?namespace=dynamic-us"
                    )
                },
                {
                    "href": (
                        "https://us.api.blizzard.com/data/wow/"
                        "connected-realm/2?namespace=dynamic-us"
                    )
                },
            ]
        }

    def get_connected_realm(self, region, connected_realm_id):
        return {
            "realms": [
                {
                    "id": 1,
                    "name": "realm1",
                    "slug": "realm-1",
                    "timezone": "America/New_York",
                    "locale": "en_US",
                },
                {
                    "id": 2,
                    "name": "realm2",
                    "slug": "realm-2",
                    "timezone": "America/New_York",
                    "locale": "en_US",
                },
            ]
        }

    def get_auctions(self, region, connected_realm_id, auction_house_id=None):
        return {
            "_links": {},
            "connected_realm": {},
            "commodities": {},
            "auctions": [
                {
                    "id": 1,
                    "item": {"id": 123},
                    "buyout": 1000,
                    "quantity": 1,
                    "time_left": "VERY_LONG",
                },
                {
                    "id": 2,
                    "item": {"id": 123},
                    "buyout": 2000,
                    "quantity": 1,
                    "time_left": "VERY_LONG",
                },
            ],
        }

    def get_commodities(self, region):
        return {
            "_links": {},
            "auctions": [
                {
                    "id": 1,
                    "item": {"id": 123},
                    "quantity": 1,
                    "unit_price": 1000,
                    "time_left": "VERY_LONG",
                },
                {
                    "id": 2,
                    "item": {"id": 123},
                    "quantity": 1,
                    "unit_price": 2000,
                    "time_left": "VERY_LONG",
                },
            ],
        }


class TestWorkflow(TestCase):
    @classmethod
    def mock_request_commodities_single_item(cls, item_id, item_price_groups):
        shuffle(item_price_groups)
        return {
            "auctions": [
                {
                    # this is the auction id, we don't care
                    "id": 1,
                    "item": {"id": item_id},
                    "quantity": price_group[1],
                    "unit_price": price_group[0],
                    "time_left": "VERY_LONG",
                }
                for price_group in item_price_groups
            ]
        }

    @classmethod
    def mock_request_commodities_multiple_items(cls, map_id_target_mv):
        return {
            "auctions": [
                {
                    # this is the auction id, we don't care
                    "id": 1,
                    "item": {"id": item_id},
                    "quantity": randint(1, 10),
                    "unit_price": target_mv,
                    "time_left": "VERY_LONG",
                }
                for item_id, target_mv in map_id_target_mv.items()
                for _ in range(randint(1, 10))
            ]
        }

    # TODO: test remove expired, test save load data integrity (include orderr)
    def assert_workflow(self, temp_path, ns_cate, game_ver, price_groups, expected_mv):
        # we only expect one entry (unique item id) in this test, if price group not
        # present, then there's no item id
        expected_number_of_entries = 1 if price_groups else 0
        # basically numbers of updates for that item
        expected_number_of_records = 1 if price_groups else 0
        item_id = "123"
        region = "us"
        namespace = Namespace(
            category=ns_cate,
            game_version=game_ver,
            region=region,
        )
        task_manager = Updater(BNAPI(wrapper=DummyAPIWrapper()), AuctionDB(temp_path))
        file = task_manager.db.get_file(namespace, DBTypeEnum.COMMODITIES)
        resp = CommoditiesResponse.parse_obj(
            self.mock_request_commodities_single_item(item_id, price_groups)
        )
        timestamp = resp.timestamp
        increments = MapItemStringMarketValueRecord.from_response(resp)
        task_manager.db.update_db(file, increments, timestamp)

        map_item_string_records = MapItemStringMarketValueRecords.from_file(file)
        self.assertEqual(expected_number_of_entries, len(map_item_string_records))

        item_string = ItemString(
            type=ItemStringTypeEnum.ITEM, id=item_id, bonuses=None, mods=None
        )
        item_records = map_item_string_records[item_string]
        self.assertEqual(expected_number_of_records, len(item_records))

        if expected_number_of_records:
            record = item_records[0]
            self.assertEqual(timestamp, record.timestamp)
            self.assertEqual(expected_mv, record.market_value)

    def test_workflow(self):
        price_groups = [
            (5, 1),
            (13, 2),
            (15, 3),
            (16, 1),
            (17, 2),
            (19, 1),
            (20, 6),
            (21, 2),
            (29, 1),
            (45, 2),
            (46, 1),
            (47, 1),
            (100, 1),
        ]
        expected_mv = 14
        temp = TemporaryDirectory()
        cate = NameSpaceCategoriesEnum.STATIC
        game_ver = GameVersionEnum.RETAIL
        with temp:
            self.assert_workflow(temp.name, cate, game_ver, price_groups, expected_mv)

    def test_workflow_edge(self):
        price_groups = []
        expected_mv = None
        temp = TemporaryDirectory()
        cate = NameSpaceCategoriesEnum.DYNAMIC
        game_ver = GameVersionEnum.RETAIL
        with temp:
            self.assert_workflow(temp.name, cate, game_ver, price_groups, expected_mv)

    def test_work_flow_basic_integrity(self):
        temp = TemporaryDirectory()
        db = AuctionDB(temp.name)
        task_manager = Updater(
            BNAPI(wrapper=DummyAPIWrapper()),
            db,
        )
        region = "us"
        namespace = Namespace(
            category=NameSpaceCategoriesEnum.STATIC,
            game_version=GameVersionEnum.RETAIL,
            region=region,
        )
        with temp:
            item_count = 100
            test_data = {str(id): randint(1000, 4000) for id in range(0, item_count)}
            test_resp = self.mock_request_commodities_multiple_items(test_data)
            test_resp = CommoditiesResponse.parse_obj(test_resp)
            """
            >>> test_resp = [
                {
                    "item": {"id": 1},
                    "quantity": 10,
                    "unit_price": 1000,
                },
                {
                    "item": {"id": 1},
                    "quantity": 41,
                    "unit_price": 1000,
                },
                {
                    "item": {"id": 2},
                    "quantity": 10,
                    "unit_price": 2200,
                },
                ...
            ]
            """
            # how many different items
            expected_item_entries = item_count
            # number of updates for each item
            # expected_item_records = 1

            timestamp = test_resp.timestamp
            crid = 123
            file = task_manager.db.get_file(namespace, DBTypeEnum.AUCTIONS, crid)
            increments = MapItemStringMarketValueRecord.from_response(test_resp)

            for i in range(1, 10):
                map_id_records = task_manager.db.update_db(
                    file, increments, test_resp.timestamp
                )
                # map_id_records = MapItemStringMarketValueRecords.from_file(file)
                self.assertEqual(expected_item_entries, len(map_id_records))

                for item_string, records in map_id_records.items():
                    # print(item_string, records)
                    self.assertEqual(i, len(records))

                    for record in records:
                        self.assertEqual(timestamp, record.timestamp)
                        self.assertEqual(
                            test_data[str(item_string)], record.market_value
                        )

    # patch time.time() to return a fixed value
    @mock.patch("time.time", return_value=1000)
    def test_work_flow_2(self, *args):
        temp = TemporaryDirectory()

        region = "us"
        game_version = GameVersionEnum.RETAIL
        db_path = f"{temp.name}/db"
        bn_api = BNAPI(wrapper=DummyAPIWrapper())
        with temp:
            main(
                db_path,
                game_version,
                region,
                None,
                bn_api,
            )
            # get all files under db_path
            files = set(os.listdir(db_path))
            expected = {
                "dynamic-us_meta.json",
                "dynamic-us_auctions_1.gz",
                "dynamic-us_auctions_2.gz",
                "dynamic-us_commodities.gz",
            }
            self.assertSetEqual(expected, files)

    def test_parse_args(self):
        raw_args = [
            "--db_path",
            "db",
            "--game_version",
            "classic_wlk",
            "us",
        ]
        args = parse_args(raw_args)
        self.assertEqual(args.region, RegionEnum.US)
        self.assertEqual(args.db_path, "db")
        self.assertEqual(args.game_version, GameVersionEnum.CLASSIC_WLK)
