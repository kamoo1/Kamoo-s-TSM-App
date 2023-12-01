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
    Realm,
    Meta,
    DBFileName,
)
from ah.db import DBHelper
from ah.updater import main as updater_main, parse_args as updater_parse_args
from ah.tsm_exporter import main as exporter_main, parse_args as exporter_parse_args
from ah.fs import ensure_path
from ah.defs import SECONDS_IN
from ah.storage import BinaryFile


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
            "id": connected_realm_id,
            "realms": [
                {
                    "id": connected_realm_id * 10 + 1,
                    "name": f"realm{connected_realm_id * 10 + 1}",
                    "slug": "",
                    "timezone": "America/New_York",
                    "locale": "en_US",
                    "region": region,
                    "connected_realm": {},
                    "category": ""
                    if connected_realm_id % 2
                    else Meta.ALL_CATE_HARDCORE[0],
                    "type": "",
                    "is_tournament": False,
                },
                {
                    "id": connected_realm_id * 10 + 2,
                    "name": f"realm{connected_realm_id * 10 + 2}",
                    "slug": "",
                    "timezone": "America/New_York",
                    "locale": "en_US",
                    "region": region,
                    "connected_realm": {},
                    "category": ""
                    if connected_realm_id % 2
                    else Meta.ALL_CATE_HARDCORE[0],
                    "type": "",
                    "is_tournament": False,
                },
            ],
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
    def assert_updater_workflow(
        self, temp_path, ns_cate, game_ver, price_groups, expected_mv
    ):
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
        db_helper = DBHelper(temp_path)
        updater = Updater(DummyAPIWrapper(), db_helper, forker=None)
        file = db_helper.get_file(namespace, DBTypeEnum.COMMODITIES)
        resp = CommoditiesResponse.model_validate(
            self.mock_request_commodities_single_item(item_id, price_groups)
        )
        timestamp = resp.timestamp
        increments = MapItemStringMarketValueRecord.from_response(resp)
        updater.save_increment(file, increments, timestamp)

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

    def test_updater_1(self):
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
            self.assert_updater_workflow(
                temp.name, cate, game_ver, price_groups, expected_mv
            )

    def test_updater_edge(self):
        price_groups = []
        expected_mv = None
        temp = TemporaryDirectory()
        cate = NameSpaceCategoriesEnum.DYNAMIC
        game_ver = GameVersionEnum.RETAIL
        with temp:
            self.assert_updater_workflow(
                temp.name, cate, game_ver, price_groups, expected_mv
            )

    def test_updater_integrity(self):
        temp = TemporaryDirectory()
        db_helper = DBHelper(temp.name)
        updater = Updater(
            DummyAPIWrapper(),
            db_helper,
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
            test_resp = CommoditiesResponse.model_validate(test_resp)
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
            file = db_helper.get_file(namespace, DBTypeEnum.AUCTIONS, crid)
            increments = MapItemStringMarketValueRecord.from_response(test_resp)

            for i in range(1, 10):
                map_id_records = updater.save_increment(
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
    def test_updater_2(self, *args):
        temp = TemporaryDirectory()

        region = "us"
        game_version = GameVersionEnum.RETAIL
        db_path = f"{temp.name}/db"
        bn_api = DummyAPIWrapper()
        with temp:
            updater_main(
                db_path=db_path,
                repo=None,
                gh_proxy=None,
                game_version=game_version,
                region=region,
                cache=None,
                gh_api=None,
                bn_api=bn_api,
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

    def test_updater_parse_args(self):
        raw_args = [
            "--db_path",
            "db",
            "--game_version",
            "classic_wlk",
            "us",
        ]
        args = updater_parse_args(raw_args)
        self.assertEqual(args.region, RegionEnum.US)
        self.assertEqual(args.db_path, "db")
        self.assertEqual(args.game_version, GameVersionEnum.CLASSIC_WLK)

    def test_exporter_parse_args(self):
        wow_folders = [
            "_classic_",
            "_retail_",
        ]
        expected_repo = "https://github.com/user/repo"
        expected_gh_proxy = "https://ghproxy.com"
        expected_db_path = "db"

        temp = TemporaryDirectory()
        with temp:
            expected_wow_base = f"{temp.name}/wow"
            for folder in wow_folders:
                ensure_path(f"{expected_wow_base}/{folder}")
            raw_args = [
                "--db_path",
                f"{expected_db_path}",
                "--repo",
                f"{expected_repo}",
                "--gh_proxy",
                f"{expected_gh_proxy}",
                "--game_version",
                "classic_wlk",
                "--warcraft_base",
                f"{expected_wow_base}",
                "us",
                "realm1",
                "realm2",
            ]
            args = exporter_parse_args(raw_args)

        self.assertEqual(args.db_path, expected_db_path)
        self.assertEqual(args.repo, expected_repo)
        self.assertEqual(args.gh_proxy, expected_gh_proxy)
        self.assertEqual(args.game_version, GameVersionEnum.CLASSIC_WLK)
        self.assertEqual(args.warcraft_base, expected_wow_base)
        self.assertEqual(args.export_region, RegionEnum.US)
        self.assertEqual(args.export_realms, {"realm1", "realm2"})

    def test_update_and_export(self):
        temp = TemporaryDirectory()
        wow_folder = "_classic_era_"
        db_path = f"{temp.name}/db"
        with temp:
            wow_base = f"{temp.name}/wow"
            ensure_path(f"{wow_base}/{wow_folder}")
            lua_path = (
                f"{wow_base}/{wow_folder}/Interface/AddOns/"
                "TradeSkillMaster_AppHelper/AppData.lua"
            )

            raw_args = [
                "--db_path",
                f"{db_path}",
                "--game_version",
                "classic",
                "us",
            ]
            args = updater_parse_args(raw_args)
            bn_api = DummyAPIWrapper()
            updater_main(**vars(args), bn_api=bn_api)

            raw_args = [
                "--db_path",
                f"{db_path}",
                "--game_version",
                "classic",
                "--warcraft_base",
                f"{wow_base}",
                "us",
                "realm11",
                "realm12",
            ]
            args = exporter_parse_args(raw_args)
            exporter_main(**vars(args))
            with open(lua_path) as f:
                content = f.read()

            expected_occurances = [
                ("AUCTIONDB_REGION_STAT", 1),
                ("AUCTIONDB_REGION_HISTORICAL", 1),
                ("Classic-US", 2),
                ("Hardcore-US", 0),
                ("AUCTIONDB_REGION_COMMODITY", 0),
                # (horde, alliance) x (realm11, realm12)
                ("AUCTIONDB_REALM_HISTORICAL", 4),
                ("AUCTIONDB_REALM_SCAN_STAT", 4),
                ("AUCTIONDB_REALM_DATA", 4),
            ]
            for expected, count in expected_occurances:
                self.assertEqual(content.count(expected), count)

    def test_update_and_export_hc(self):
        temp = TemporaryDirectory()
        wow_folder = "_classic_era_"
        db_path = f"{temp.name}/db"
        with temp:
            wow_base = f"{temp.name}/wow"
            ensure_path(f"{wow_base}/{wow_folder}")
            lua_path = (
                f"{wow_base}/{wow_folder}/Interface/AddOns/"
                "TradeSkillMaster_AppHelper/AppData.lua"
            )

            raw_args = [
                "--db_path",
                f"{db_path}",
                "--game_version",
                "classic",
                "us",
            ]
            args = updater_parse_args(raw_args)
            bn_api = DummyAPIWrapper()
            updater_main(**vars(args), bn_api=bn_api)

            raw_args = [
                "--db_path",
                f"{db_path}",
                "--game_version",
                "classic",
                "--warcraft_base",
                f"{wow_base}",
                "us",
                "realm21",
                "realm22",
            ]
            args = exporter_parse_args(raw_args)
            exporter_main(**vars(args))
            with open(lua_path) as f:
                content = f.read()

            expected_occurances = [
                ("AUCTIONDB_REGION_STAT", 1),
                ("AUCTIONDB_REGION_HISTORICAL", 1),
                ("Classic-US", 0),
                ("HC-US", 2),
                ("AUCTIONDB_REGION_COMMODITY", 0),
                # (horde, alliance) x (realm11, realm12)
                ("AUCTIONDB_REALM_HISTORICAL", 4),
                ("AUCTIONDB_REALM_SCAN_STAT", 4),
                ("AUCTIONDB_REALM_DATA", 4),
            ]
            for expected, count in expected_occurances:
                self.assertEqual(content.count(expected), count)

    @mock.patch("time.time")
    @mock.patch.object(MapItemStringMarketValueRecords, "update_increment")
    @mock.patch.object(MapItemStringMarketValueRecords, "remove_expired")
    @mock.patch.object(MapItemStringMarketValueRecords, "compress")
    def test_updater_ts_compressed_remote_mode_meta_hit(self, m1, m2, m3, m4):
        """
        local mode (forker is None):
                    | data hit  | data miss
        ----------------------------------------
        meta hit    | tsc=local | ts=0
        meta miss   | tsc=0     | ts=0

        note that for meta miss + data miss case, tsc (`ts_compress`)
        did not set to 0 during `save_increment` call, it was set to 0
        in `update_region` as default value.

        remote mode (forker is not None):
                    | data hit      | data miss
        ----------------------------------------
        meta hit    | ts=local      | ts=0
        meta miss   | ts=0          | ts=remote

        """
        m1.return_value = 1  # compress
        m2.return_value = 1  # remove_expired
        m3.return_value = (1, 1)  # update_increment
        m4.return_value = SECONDS_IN.DAY * 2  # time.time

        """if `ts_compressed` coming from local meta file, then remote db file's
        `ts_compressed` should be 0
        """
        temp = TemporaryDirectory()
        meta_file_path = f"{temp.name}/dynamic-us_meta.json"
        meta_file_name = os.path.basename(meta_file_path)

        db_file_path = f"{temp.name}/dynamic-us_auctions_1.gz"
        db_file_name = os.path.basename(db_file_path)

        db_helper = DBHelper(temp.name)
        updater = Updater(DummyAPIWrapper(), db_helper, forker=mock.MagicMock())
        with temp:
            # create local meta and local db (crid=1)
            # crid 2 & commodities will be remote
            meta = Meta()
            meta.set_update_ts(SECONDS_IN.DAY + 1000, SECONDS_IN.DAY + 2000)
            meta_fn = DBFileName.from_str(meta_file_name)
            meta_file = db_helper.get_file(
                meta_fn.namespace,
                meta_fn.db_type,
                crid=meta_fn.crid,
                faction=meta_fn.faction,
            )
            meta.to_file(meta_file)
            db = MapItemStringMarketValueRecords()
            db_fn = DBFileName.from_str(db_file_name)
            db_file = db_helper.get_file(
                db_fn.namespace,
                db_fn.db_type,
                crid=db_fn.crid,
                faction=db_fn.faction,
            )
            db.to_file(db_file)

            ns = Namespace.from_str("dynamic-us")
            updater.update_region(ns)

            self.assertEqual(3, m1.call_count)
            m1.assert_has_calls(
                [
                    # crid=1 (local db)
                    mock.call(
                        SECONDS_IN.DAY * 2,
                        Updater.RECORDS_EXPIRES_IN,
                        ts_compressed=SECONDS_IN.DAY,
                    ),
                    # crid=2 (forked remote db)
                    mock.call(
                        SECONDS_IN.DAY * 2,
                        Updater.RECORDS_EXPIRES_IN,
                        ts_compressed=0,
                    ),
                    # commodities (forked remote db)
                    mock.call(
                        SECONDS_IN.DAY * 2,
                        Updater.RECORDS_EXPIRES_IN,
                        ts_compressed=0,
                    ),
                ]
            )

    @mock.patch("time.time")
    @mock.patch.object(MapItemStringMarketValueRecords, "update_increment")
    @mock.patch.object(MapItemStringMarketValueRecords, "remove_expired")
    @mock.patch.object(MapItemStringMarketValueRecords, "compress")
    def test_updater_ts_compressed_remote_mode_meta_miss(self, m1, m2, m3, m4):
        m1.return_value = 1  # compress
        m2.return_value = 1  # remove_expired
        m3.return_value = (1, 1)  # update_increment
        m4.return_value = SECONDS_IN.DAY * 2  # time.time

        """if `ts_compressed` coming from remote db file, then local db file's
        `ts_compressed` should be 0
        """
        temp = TemporaryDirectory()
        db_file_path = f"{temp.name}/dynamic-us_auctions_1.gz"
        db_file_name = os.path.basename(db_file_path)

        db_helper = DBHelper(temp.name)
        forker = mock.MagicMock()

        def ensure_file(file):
            if isinstance(file, BinaryFile):
                MapItemStringMarketValueRecords().to_file(file)
            else:
                meta = Meta()
                meta.set_update_ts(SECONDS_IN.DAY + 1000, SECONDS_IN.DAY + 2000)
                meta.to_file(file)

        forker.ensure_file.side_effect = ensure_file
        updater = Updater(DummyAPIWrapper(), db_helper, forker=forker)
        with temp:
            # create local db (crid=1)
            # crid 2 & commodities will be remote
            # meta file will be remote
            db = MapItemStringMarketValueRecords()
            db_fn = DBFileName.from_str(db_file_name)
            db_file = db_helper.get_file(
                db_fn.namespace,
                db_fn.db_type,
                crid=db_fn.crid,
                faction=db_fn.faction,
            )
            db.to_file(db_file)

            ns = Namespace.from_str("dynamic-us")
            updater.update_region(ns)

            self.assertEqual(3, m1.call_count)
            m1.assert_has_calls(
                [
                    # crid=1 (local db)
                    mock.call(
                        SECONDS_IN.DAY * 2,
                        Updater.RECORDS_EXPIRES_IN,
                        ts_compressed=0,
                    ),
                    # crid=2 (forked remote db)
                    mock.call(
                        SECONDS_IN.DAY * 2,
                        Updater.RECORDS_EXPIRES_IN,
                        ts_compressed=SECONDS_IN.DAY,
                    ),
                    # commodities (forked remote db)
                    mock.call(
                        SECONDS_IN.DAY * 2,
                        Updater.RECORDS_EXPIRES_IN,
                        ts_compressed=SECONDS_IN.DAY,
                    ),
                ]
            )
