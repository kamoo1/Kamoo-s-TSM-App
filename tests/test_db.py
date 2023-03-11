from unittest import TestCase
import tempfile
import json

from ah.db import AuctionDB
from ah.models import (
    MapItemStringMarketValueRecord,
    MapItemStringMarketValueRecords,
    MarketValueRecord,
    ItemString,
    ItemStringTypeEnum,
)


class DummyGHAPI:
    API_TEMPLATE = "https://api.github.com/repos/{user}/{repo}/releases/latest"

    def __init__(
        self,
        site: str,
        region: str,
        n_crid: int,
        n_item: int,
        n_record_per_item: int,
        ts_base: int,
    ) -> None:
        self.site = site
        self.region = region
        self.n_crid = n_crid
        db = MapItemStringMarketValueRecords()

        for i_item in range(n_item):
            for i_record in range(n_record_per_item):
                db.add_market_value_record(
                    ItemString(
                        type=ItemStringTypeEnum.ITEM,
                        id=i_item,
                        bonuses=None,
                        mods=None,
                    ),
                    MarketValueRecord(
                        timestamp=ts_base + i_record,
                        market_value=1,
                        num_auctions=1,
                        min_buyout=1,
                    ),
                )
        self.db_bytes = db.to_protobuf_bytes()

    def get_assets_uri(self, owner, repo):
        ret = {}
        for n in range(self.n_crid):
            file_name = AuctionDB.FN_CRID_AUCTIONS.format(
                region=self.region, crid=n, suffix="gz"
            )
            ret[file_name] = f"{self.site}/{file_name}"

        meta_file_name = AuctionDB.FN_META.format(region=self.region)
        ret[meta_file_name] = f"{self.site}/{meta_file_name}"
        return ret

    def get_asset(self, url: str) -> bytes:
        assert url.startswith(self.site)
        if url.endswith("json"):
            # meta file
            meta = {
                "start_ts": 1,
                "end_ts": 2,
                "duration": 1,
            }
            return json.dumps(meta).encode()
        else:
            return self.db_bytes


class TestAuctionDB(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_init(self):
        db_path = self.tmp_dir.name
        expires = AuctionDB.MIN_RECORDS_EXPIRES_IN
        compress = True
        site = "https://example.com"
        region = "us"
        ts_base = 1000
        gh_api = DummyGHAPI(site, region, 2, 2, 2, ts_base)
        fork_repo = "github.com/user/repo"

        # expires time too short
        AuctionDB(db_path, expires, compress)
        self.assertRaises(
            ValueError,
            AuctionDB,
            db_path,
            expires - 1,
            compress,
        )

        # invalid mode
        AuctionDB(db_path, expires, compress, AuctionDB.MODE_LOCAL_RW)
        self.assertRaises(
            ValueError,
            AuctionDB,
            db_path,
            expires,
            compress,
            "invalid_mode",
        )

        # remote mode without fork_repo and gh_api
        AuctionDB(
            db_path,
            expires,
            compress,
            AuctionDB.MODE_REMOTE_R,
            fork_repo=fork_repo,
            gh_api=gh_api,
        )
        self.assertRaises(
            ValueError,
            AuctionDB,
            db_path,
            expires,
            compress,
            AuctionDB.MODE_REMOTE_R,
        )
        self.assertRaises(
            ValueError,
            AuctionDB,
            db_path,
            expires,
            compress,
            AuctionDB.MODE_REMOTE_R,
            fork_repo=fork_repo,
        )

        # invalid fork_repo
        self.assertRaises(
            ValueError,
            AuctionDB,
            db_path,
            expires,
            compress,
            AuctionDB.MODE_REMOTE_R,
            fork_repo="invalid_repo",
            gh_api=gh_api,
        )

    def assert_db(
        self,
        db: AuctionDB,
        region: str,
        n_crid: int,
        n_item: int,
        n_record_per_item: int,
    ):
        for crid in range(n_crid):
            file = db.get_db_file(region, crid)
            map_records = db.load_db(file)
            self.assertEqual(len(map_records), n_item)
            for item_string in map_records:
                self.assertEqual(len(map_records[item_string]), n_record_per_item)

    def test_mode_remote(self):
        mode = AuctionDB.MODE_REMOTE_R
        db_path = self.tmp_dir.name
        expires = AuctionDB.MIN_RECORDS_EXPIRES_IN
        compress = True
        fork_repo = "github.com/user/repo"

        site = "https://example.com"
        region = "us"
        n_crid = n_item = n_record_per_item = 2
        ts_base = 1000
        gh_api = DummyGHAPI(site, region, n_crid, n_item, n_record_per_item, ts_base)

        db = AuctionDB(
            db_path,
            expires,
            compress,
            mode,
            fork_repo=fork_repo,
            gh_api=gh_api,
        )
        self.assert_db(db, region, n_crid, n_item, n_record_per_item)

        # test meta file
        meta_file = db.get_meta_file(region)
        meta = db.load_meta(meta_file)
        self.assertEqual(meta["duration"], 1)

        # assert raises when trying to update meta
        self.assertRaises(ValueError, db.update_meta, meta_file, 2, 3)

        # pick one of the db file for testing
        pick_crid = n_crid - 1
        pick_file = db.get_db_file(region, pick_crid)
        pick_map = db.load_db(pick_file)

        # assert raises when file not in remote
        bad_file = db.get_db_file(region + "that_not_exist", pick_crid)
        self.assertRaises(FileNotFoundError, db.fork_file, bad_file)
        self.assertFalse(db.load_db(bad_file))  # return empty map

        # assert raises when trying to update
        increment = MapItemStringMarketValueRecord()
        self.assertRaises(ValueError, db.update_db, pick_file, increment, ts_base)

        # force update local
        new_item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=n_item,
            bonuses=None,
            mods=None,
        )
        pick_map[new_item_string].add(
            MarketValueRecord(
                timestamp=ts_base + n_record_per_item,
                market_value=1,
                num_auctions=1,
                min_buyout=1,
            )
        )
        pick_map.to_file(pick_file)
        self.assertEqual(len(pick_map), n_item + 1)

        # assert local changes discarded
        db = AuctionDB(
            db_path,
            expires,
            compress,
            AuctionDB.MODE_REMOTE_R,
            fork_repo=fork_repo,
            gh_api=gh_api,
        )
        pick_map_ = db.load_db(pick_file)
        self.assertEqual(len(pick_map_), n_item)
        self.assert_db(db, region, n_crid, n_item, n_record_per_item)

    def test_mode_local_remote(self):
        mode = AuctionDB.MODE_LOCAL_REMOTE_RW
        db_path = self.tmp_dir.name
        expires = AuctionDB.MIN_RECORDS_EXPIRES_IN
        compress = True
        fork_repo = "github.com/user/repo"

        site = "https://example.com"
        region = "us"
        n_crid = n_item = n_record_per_item = 2
        ts_base = 1000
        gh_api = DummyGHAPI(site, region, n_crid, n_item, n_record_per_item, ts_base)

        db = AuctionDB(
            db_path,
            expires,
            compress,
            mode,
            fork_repo=fork_repo,
            gh_api=gh_api,
        )
        self.assert_db(db, region, n_crid, n_item, n_record_per_item)

        # pick one of the db file for testing
        pick_crid = n_crid - 1
        pick_file = db.get_db_file(region, pick_crid)

        # update local
        new_item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=n_item,
            bonuses=None,
            mods=None,
        )
        new_record = MarketValueRecord(
            timestamp=1000,
            market_value=1,
            num_auctions=1,
            min_buyout=1,
        )
        increment = MapItemStringMarketValueRecord(
            __root__={new_item_string: new_record}
        )
        db.update_db(pick_file, increment, ts_base + n_record_per_item)
        pick_map = db.load_db(pick_file)
        self.assertEqual(len(pick_map), n_item + 1)

        # update meta file
        meta_file = db.get_meta_file(region)
        db.update_meta(meta_file, 2, 3)

        # assert local changes are kept
        db = AuctionDB(
            db_path,
            expires,
            compress,
            mode,
            fork_repo=fork_repo,
            gh_api=gh_api,
        )
        pick_map = db.load_db(pick_file)
        self.assertEqual(len(pick_map), n_item + 1)
        meta = db.load_meta(meta_file)

        # assert local changes in meta
        self.assertEqual(meta["start_ts"], 2)
        self.assertEqual(meta["end_ts"], 3)
        self.assertEqual(meta["duration"], 1)

    def test_local(self):
        mode = AuctionDB.MODE_LOCAL_RW
        db_path = self.tmp_dir.name
        expires = AuctionDB.MIN_RECORDS_EXPIRES_IN
        compress = True
        region = "tw"

        db = AuctionDB(
            db_path,
            expires,
            compress,
            mode,
        )
        self.assert_db(db, region, 0, 0, 0)

        # pick one of the db file for testing
        pick_crid = 1
        pick_file = db.get_db_file(region, pick_crid)
        pick_item_id = 1
        pick_ts = 1000

        # update local
        new_item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=pick_item_id,
            bonuses=None,
            mods=None,
        )
        new_record = MarketValueRecord(
            timestamp=1000,
            market_value=1,
            num_auctions=1,
            min_buyout=1,
        )
        increment = MapItemStringMarketValueRecord(
            __root__={new_item_string: new_record}
        )
        db.update_db(pick_file, increment, pick_ts)
        pick_map = db.load_db(pick_file)
        self.assertEqual(len(pick_map), 1)

        # assert local changes are kept
        db = AuctionDB(
            db_path,
            expires,
            compress,
            mode,
        )
        pick_map = db.load_db(pick_file)
        self.assertEqual(len(pick_map), 1)
