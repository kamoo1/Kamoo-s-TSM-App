from unittest import TestCase
from typing import Optional
import tempfile
import json
import gzip

from ah.errors import DownloadError
from ah.db import DBHelper, GithubFileForker
from ah.updater import Updater
from ah.models import (
    MapItemStringMarketValueRecord,
    MapItemStringMarketValueRecords,
    MarketValueRecord,
    ItemString,
    ItemStringTypeEnum,
    Namespace,
    DBTypeEnum,
    NameSpaceCategoriesEnum,
    GameVersionEnum,
    DBFileName,
    DBExtEnum,
    FactionEnum,
    Meta,
)


class DummyGHAPI:
    API_TEMPLATE = "https://api.github.com/repos/{user}/{repo}/releases/latest"

    def __init__(
        self,
        site: str,
        category: NameSpaceCategoriesEnum,
        game_version: GameVersionEnum,
        region: str,
        n_crid: int,
        n_item: int,
        n_record_per_item: int,
        ts_base: int,
        faction: Optional[FactionEnum] = None,
    ) -> None:
        self.site = site
        self.category = category
        self.game_version = game_version
        self.region = region
        self.n_crid = n_crid
        self.faction = faction
        db = MapItemStringMarketValueRecords()

        if self.game_version != GameVersionEnum.RETAIL and self.faction is None:
            raise ValueError(
                f"faction must be specified for game_version={game_version!r}"
            )

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
        self.db_bytes = gzip.compress(self.db_bytes)

    def get_assets_uri(self, owner, repo, tag=None):
        ret = {}
        namespace = Namespace(
            category=self.category,
            game_version=self.game_version,
            region=self.region,
        )

        for n in range(self.n_crid):
            file_name = DBFileName(
                namespace=namespace,
                db_type=DBTypeEnum.AUCTIONS,
                crid=n,
                faction=self.faction,
                ext=DBExtEnum.GZ,
            )
            ret[str(file_name)] = f"{self.site}/{file_name}"

        meta_file_name = DBFileName(
            namespace=namespace,
            db_type=DBTypeEnum.META,
            ext=DBExtEnum.JSON,
        )
        ret[str(meta_file_name)] = f"{self.site}/{meta_file_name}"

        if self.game_version == GameVersionEnum.RETAIL:
            commodity_file_name = DBFileName(
                namespace=namespace,
                db_type=DBTypeEnum.COMMODITIES,
                ext=DBExtEnum.GZ,
            )
            ret[str(commodity_file_name)] = f"{self.site}/{commodity_file_name}"
        return ret

    def get_asset(self, url: str) -> bytes:
        assert url.startswith(self.site)
        if url.endswith("json"):
            # meta file
            meta = {
                "update": {
                    "start_ts": 1,
                    "end_ts": 2,
                    "duration": 1,
                },
                "connected_realms": {},
                "system": {},
            }
            return json.dumps(meta).encode()
        else:
            return self.db_bytes


class TestAuctionDB(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def assert_db(
        self,
        db_helper: DBHelper,
        category: NameSpaceCategoriesEnum,
        game_version: GameVersionEnum,
        region: str,
        n_crid: int,
        n_item: int,
        n_record_per_item: int,
        faction: Optional[FactionEnum] = None,
        forker: Optional[GithubFileForker] = None,
    ):
        namespace = Namespace(
            category=category,
            game_version=game_version,
            region=region,
        )
        for crid in range(n_crid):
            file = db_helper.get_file(
                namespace, DBTypeEnum.AUCTIONS, crid=crid, faction=faction
            )
            map_records = MapItemStringMarketValueRecords.from_file(file, forker=forker)
            self.assertEqual(len(map_records), n_item)
            for item_string in map_records:
                self.assertEqual(len(map_records[item_string]), n_record_per_item)

    def test_fork(self):
        db_path = self.tmp_dir.name
        fork_repo = "github.com/user/repo"

        site = "https://example.com"
        region = "us"
        n_crid = n_item = n_record_per_item = 2
        ts_base = 1000
        category = NameSpaceCategoriesEnum.STATIC
        game_version = GameVersionEnum.CLASSIC
        namespace = Namespace(
            category=category,
            game_version=game_version,
            region=region,
        )
        faction = FactionEnum.HORDE
        gh_api = DummyGHAPI(
            site,
            category,
            game_version,
            region,
            n_crid,
            n_item,
            n_record_per_item,
            ts_base,
            faction=faction,
        )

        db_helper = DBHelper(db_path)
        forker = GithubFileForker(db_path, fork_repo, gh_api)
        self.assert_db(
            db_helper,
            category,
            game_version,
            region,
            n_crid,
            n_item,
            n_record_per_item,
            faction=faction,
            forker=forker,
        )

        # test meta file
        meta_file = db_helper.get_file(namespace, DBTypeEnum.META)
        meta = Meta.from_file(meta_file, forker=forker)
        self.assertEqual(meta.get_update_ts(), (1, 2))

        # pick one of the db file for testing
        pick_crid = n_crid - 1
        pick_file = db_helper.get_file(
            namespace,
            DBTypeEnum.AUCTIONS,
            crid=pick_crid,
            faction=faction,
        )
        pick_map = MapItemStringMarketValueRecords.from_file(pick_file, forker=forker)

        # assert raises when file not in remote
        bad_file = db_helper.get_file(
            namespace,
            DBTypeEnum.AUCTIONS,
            crid=n_crid + 1,
            faction=faction,
        )
        self.assertRaises(DownloadError, forker._fork_file, bad_file)
        self.assertFalse(MapItemStringMarketValueRecords.from_file(bad_file, forker))

        # force update local
        # NOTE: use to be a follow up "load" call that overwrites these changes
        #       to test out the "remote only" mode, but that mode is removed
        #       so here's this force update left over
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

    def test_mode_local_remote(self):
        db_path = self.tmp_dir.name
        fork_repo = "github.com/user/repo"

        site = "https://example.com"
        region = "us"
        n_crid = n_item = n_record_per_item = 2
        ts_base = 1000
        category = NameSpaceCategoriesEnum.STATIC
        game_version = GameVersionEnum.CLASSIC
        namespace = Namespace(
            category=category,
            game_version=game_version,
            region=region,
        )
        faction = FactionEnum.ALLIANCE
        gh_api = DummyGHAPI(
            site,
            category,
            game_version,
            region,
            n_crid,
            n_item,
            n_record_per_item,
            ts_base,
            faction=faction,
        )
        db_helper = DBHelper(db_path)
        forker = GithubFileForker(db_path, fork_repo, gh_api)
        self.assert_db(
            db_helper,
            category,
            game_version,
            region,
            n_crid,
            n_item,
            n_record_per_item,
            faction=faction,
            forker=forker,
        )

        # pick one of the db file for testing
        pick_crid = n_crid - 1
        pick_file = db_helper.get_file(
            namespace,
            DBTypeEnum.AUCTIONS,
            crid=pick_crid,
            faction=faction,
        )

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
        updater = Updater({}, db_helper, forker=forker)
        updater.save_increment(pick_file, increment, ts_base + n_record_per_item)
        pick_map = MapItemStringMarketValueRecords.from_file(pick_file, forker=forker)
        self.assertEqual(len(pick_map), n_item + 1)

        # update meta file
        meta_file = db_helper.get_file(namespace, DBTypeEnum.META)
        meta = Meta.from_file(meta_file, forker=forker)
        meta._data["update"]["start_ts"] = 2
        meta._data["update"]["end_ts"] = 3
        meta.to_file(meta_file)

        # assert local changes are kept
        pick_map = MapItemStringMarketValueRecords.from_file(pick_file, forker=forker)
        self.assertEqual(len(pick_map), n_item + 1)
        meta = Meta.from_file(meta_file, forker=forker)

        # assert local changes in meta
        meta_ts = meta._data["update"]
        self.assertEqual(meta_ts["start_ts"], 2)
        self.assertEqual(meta_ts["end_ts"], 3)
        self.assertEqual(meta_ts["duration"], 1)

    def test_local(self):
        db_path = self.tmp_dir.name
        region = "tw"
        category = NameSpaceCategoriesEnum.DYNAMIC
        game_version = GameVersionEnum.CLASSIC
        namespace = Namespace(
            category=category,
            game_version=game_version,
            region=region,
        )

        db_helper = DBHelper(db_path)
        forker = None
        self.assert_db(
            db_helper, category, game_version, region, 0, 0, 0, forker=forker
        )

        # pick one of the db file for testing
        pick_crid = 1
        pick_file = db_helper.get_file(
            namespace, DBTypeEnum.AUCTIONS, crid=pick_crid, faction=FactionEnum.HORDE
        )
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
        updater = Updater({}, db_helper, forker=forker)
        updater.save_increment(pick_file, increment, pick_ts)
        pick_map = MapItemStringMarketValueRecords.from_file(pick_file, forker=forker)
        self.assertEqual(len(pick_map), 1)

        # assert local changes are kept
        pick_map = MapItemStringMarketValueRecords.from_file(pick_file, forker=forker)
        self.assertEqual(len(pick_map), 1)

    def test_load_db(self):
        # mode = AuctionManager.MODE_REMOTE_R
        db_path = self.tmp_dir.name
        fork_repo = "github.com/user/repo"

        site = "https://example.com"
        region = "us"
        n_crid = n_item = n_record_per_item = 2
        ts_base = 1000
        category = NameSpaceCategoriesEnum.DYNAMIC
        game_version = GameVersionEnum.RETAIL
        gh_api = DummyGHAPI(
            site,
            category,
            game_version,
            region,
            n_crid,
            n_item,
            n_record_per_item,
            ts_base,
        )
        namespace = Namespace(
            category=category,
            game_version=game_version,
            region=region,
        )
        db_helper = DBHelper(db_path)
        forker = GithubFileForker(db_path, fork_repo, gh_api)
        self.assert_db(
            db_helper,
            category,
            game_version,
            region,
            n_crid,
            n_item,
            n_record_per_item,
            forker=forker,
        )

        pick_crid = n_crid - 1
        pick_file = db_helper.get_file(namespace, DBTypeEnum.AUCTIONS, crid=pick_crid)
        pick_map = MapItemStringMarketValueRecords.from_file(pick_file, forker=forker)
        self.assertTrue(pick_map)

        pick_crid = None
        pick_file = db_helper.get_file(
            namespace, DBTypeEnum.COMMODITIES, crid=pick_crid
        )
        pick_map = MapItemStringMarketValueRecords.from_file(pick_file, forker=forker)
        self.assertTrue(pick_map)

    @classmethod
    def make_db_file(cls, db_helper, region, crid):
        namespace = Namespace(
            category=NameSpaceCategoriesEnum.DYNAMIC,
            game_version=GameVersionEnum.CLASSIC,
            region=region,
        )
        db_type_e = DBTypeEnum.AUCTIONS
        db_file = db_helper.get_file(
            namespace, db_type_e, crid=crid, faction=FactionEnum.ALLIANCE
        )
        db_file.touch()
        return db_file.file_name

    def test_list_db_name(self):
        db_path = self.tmp_dir.name
        region = "us"
        n_crid = 2

        db_helper = DBHelper(db_path)
        expected = set()
        for crid in range(n_crid):
            fn = self.make_db_file(db_helper, region, crid)
            expected.add(fn)
        self.assertEqual(set(db_helper.list_file()), expected)
