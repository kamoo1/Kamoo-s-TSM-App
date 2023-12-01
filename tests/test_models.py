from unittest import TestCase
from tempfile import TemporaryDirectory
import json
from copy import deepcopy

from ah.models.blizzard import (
    Namespace,
    RegionEnum,
    NameSpaceCategoriesEnum,
    GameVersionEnum,
)
from ah.models.self import (
    DBExtEnum,
    DBFileName,
    DBTypeEnum,
    FactionEnum,
    Meta,
    ConnectedRealm,
)
from ah.db import DBHelper


class TestModels(TestCase):
    def test_name_space(self):
        ns = Namespace(
            category=NameSpaceCategoriesEnum.DYNAMIC,
            game_version=GameVersionEnum.CLASSIC,
            region=RegionEnum.US,
        )
        expected = "dynamic-classic1x-us"
        self.assertEqual(ns.to_str(), expected)
        ns_ = Namespace.from_str(expected)
        self.assertTrue(ns_ == ns)

        ns = Namespace(
            category=NameSpaceCategoriesEnum.DYNAMIC,
            game_version=GameVersionEnum.RETAIL,
            region=RegionEnum.US,
        )
        self.assertEqual(ns.to_str(), "dynamic-us")
        self.assertEqual(repr(ns), '"dynamic-us"')

        ns = Namespace.from_str("dynamic-classic1x-us")
        self.assertEqual(ns.category, NameSpaceCategoriesEnum.DYNAMIC)
        self.assertEqual(ns.game_version, GameVersionEnum.CLASSIC)
        self.assertEqual(ns.region, RegionEnum.US)

        ns = Namespace.from_str("static-us")
        self.assertEqual(ns.category, NameSpaceCategoriesEnum.STATIC)
        self.assertEqual(ns.game_version, GameVersionEnum.RETAIL)
        self.assertEqual(ns.region, RegionEnum.US)

        with self.assertRaises(ValueError):
            Namespace.from_str("dynamic-xx")

        with self.assertRaises(ValueError):
            Namespace.from_str("dynamic-xx-us")

        with self.assertRaises(ValueError):
            Namespace.from_str("xx-us")

        with self.assertRaises(ValueError):
            Namespace.from_str("static-xx-us")

        with self.assertRaises(ValueError):
            Namespace.from_str("xx-classic1x-us")

        with self.assertRaises(ValueError):
            Namespace.from_str("static-classic1x-xx")

    def test_db_file_name(self):
        ns = Namespace(
            category=NameSpaceCategoriesEnum.DYNAMIC,
            game_version=GameVersionEnum.CLASSIC,
            region=RegionEnum.US,
        )
        ns_r = Namespace(
            category=NameSpaceCategoriesEnum.DYNAMIC,
            game_version=GameVersionEnum.RETAIL,
            region=RegionEnum.US,
        )

        name = DBFileName(
            namespace=ns,
            db_type=DBTypeEnum.AUCTIONS,
            crid=123,
            faction=FactionEnum.HORDE,
            ext=DBExtEnum.GZ,
        )
        expected = "dynamic-classic1x-us_auctions_123_h.gz"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)
        self.assertTrue(name.is_compress())

        name = DBFileName(
            namespace=ns,
            db_type=DBTypeEnum.META,
            ext=DBExtEnum.JSON,
        )
        expected = "dynamic-classic1x-us_meta.json"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)

        name = DBFileName(
            namespace=ns,
            db_type=DBTypeEnum.META,
            crid=None,
            ext=DBExtEnum.JSON,
        )
        expected = "dynamic-classic1x-us_meta.json"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)

        # uses json by default for meta
        name = DBFileName(
            namespace=ns,
            db_type=DBTypeEnum.META,
            ext=DBExtEnum.JSON,
        )
        expected = "dynamic-classic1x-us_meta.json"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)

        name = DBFileName(
            namespace=ns.to_str(),
            db_type="auctions",
            crid=123,
            faction=FactionEnum.ALLIANCE,
            ext="gz",
        )
        expected = "dynamic-classic1x-us_auctions_123_a.gz"

        name = DBFileName(
            namespace=ns_r,
            db_type=DBTypeEnum.COMMODITIES,
            ext=DBExtEnum.BIN,
        )
        expected = "dynamic-us_commodities.bin"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)
        self.assertFalse(name.is_compress())

        name = DBFileName(
            namespace=ns_r.to_str(),
            db_type="commodities",
            ext="bin",
        )
        expected = "dynamic-us_commodities.bin"

        with self.assertRaises(ValueError):
            DBFileName(
                namespace=ns.to_str(),
                db_type="commodities123",
                ext="bin",
            )

        with self.assertRaises(ValueError):
            DBFileName(
                namespace=ns.to_str(),
                db_type="meta123",
                ext="bin",
            )

        with self.assertRaises(ValueError):
            DBFileName(
                namespace=ns.to_str(),
                db_type="auctions 123",
                ext="bin",
            )

        with self.assertRaises(ValueError):
            DBFileName(
                namespace=ns.to_str(),
                db_type="auctions-123",
                ext="bin",
            )

        with self.assertRaises(ValueError):
            DBFileName(
                namespace=ns.to_str(),
                db_type="auctions+123",
                ext="bin",
            )

        with self.assertRaises(ValueError):
            DBFileName(
                namespace=ns.to_str(),
                db_type="auctions12.3",
                ext="bin",
            )

        with self.assertRaises(ValueError):
            DBFileName(
                namespace=ns.to_str(),
                db_type="auctions123 ",
                ext="bin",
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.COMMODITIES,
                crid=123,
                ext=DBExtEnum.GZ,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.AUCTIONS,
                crid=None,
                ext=DBExtEnum.GZ,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.AUCTIONS,
                ext=DBExtEnum.GZ,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.AUCTIONS,
                crid=123,
                ext=DBExtEnum.JSON,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.COMMODITIES,
                ext=DBExtEnum.JSON,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.META,
                ext=DBExtEnum.BIN,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.META,
                crid=123,
                ext=DBExtEnum.JSON,
            )

        with self.assertRaises(TypeError):
            # file ext is no longer optional
            name = DBFileName(
                namespace=ns,
                db_type=DBTypeEnum.META,
            )

        DBFileName.from_str("dynamic-classic1x-us_auctions_123_h.bin")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_auctions_h.bin")

        DBFileName.from_str("dynamic-us_commodities.bin")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-us_commodities_123.bin")

        DBFileName.from_str("dynamic-classic1x-us_auctions_123_a.gz")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_xxx_123_a.gz")

        DBFileName.from_str("dynamic-us_commodities.gz")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-us_commodities.xxx")

        DBFileName.from_str("dynamic-classic1x-us_auctions_123_a.gz")
        with self.assertRaises(ValueError):
            DBFileName.from_str("xxx-classic1x-us_auctions_123_a.gz")

        DBFileName.from_str("dynamic-classic1x-us_meta.json")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_meta.gz")

        DBFileName.from_str("dynamic-classic1x-us_meta.json")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_meta.bin")

        DBFileName.from_str("dynamic-classic1x-us_auctions_123_a.gz")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_auctions_123.gz")

        DBFileName.from_str("dynamic-classic1x-us_auctions_123_h.gz")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_auctions_123_x.gz")

        DBFileName.from_str("dynamic-us_auctions_123.gz")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-us_auctions_123_h.gz")

        DBFileName.from_str("dynamic-us_commodities.bin")
        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_commodities.bin")

    def test_meta_from_file(self):
        temp = TemporaryDirectory()
        with temp:
            path = temp.name
            helper = DBHelper(path)
            namespace = Namespace(
                category=NameSpaceCategoriesEnum.DYNAMIC,
                game_version=GameVersionEnum.CLASSIC,
                region=RegionEnum.US,
            )
            meta_file = helper.get_file(namespace, DBTypeEnum.META)
            meta_path = meta_file.file_path
            meta_data = {
                "update": {
                    "start_ts": 1,
                    "end_ts": 2,
                    "duration": 1,
                },
                "connected_realms": {
                    "1": [
                        {
                            "name": "realm name",
                            "id": 1,
                            "slug": "realm_name",
                            "category": "hardcore",
                        },
                    ],
                },
                "system": {},
            }
            with open(meta_path, "w") as f:
                json.dump(meta_data, f)

            # update meta data
            meta = Meta.from_file(meta_file)
            meta.set_system({"foo": "bar"})
            meta.set_update_ts(10, 20)
            cr_resp = {
                "id": 100,
                "realms": [
                    # id, region, connected_realm,
                    # name, category, locale, timezone,
                    # type, is_tournament, slug, links
                    {
                        "id": 100,
                        "region": "US",
                        "connected_realm": {},
                        "name": "realm name 1",
                        "category": "any other str",
                        "locale": "",
                        "timezone": "",
                        "type": "",
                        "is_tournament": False,
                        "slug": "",
                        "_links": {},
                    },
                    {
                        "id": 101,
                        "region": "US",
                        "connected_realm": {},
                        "name": "realm name 2",
                        "category": "any other str",
                        "locale": "",
                        "timezone": "",
                        "type": "",
                        "is_tournament": False,
                        "slug": "",
                        "_links": {},
                    }
                ],
            }
            cr = ConnectedRealm.model_validate(cr_resp)
            meta.add_connected_realm(100, cr)
            cr_resp = {
                "id": 200,
                "realms": [
                    {
                        "id": 200,
                        "region": "US",
                        "connected_realm": {},
                        "name": "realm name 1",
                        "category": "Seasonal",
                        "locale": "",
                        "timezone": "",
                        "type": "",
                        "is_tournament": False,
                        "slug": "",
                        "_links": {},
                    },
                    {
                        "id": 201,
                        "region": "US",
                        "connected_realm": {},
                        "name": "realm name 2",
                        "category": "Seasonal",
                        "locale": "",
                        "timezone": "",
                        "type": "",
                        "is_tournament": False,
                        "slug": "",
                        "_links": {},
                    }
                ],
            }
            cr = ConnectedRealm.model_validate(cr_resp)
            meta.add_connected_realm(200, cr)
            meta.to_file(meta_file)

            # update expected meta data
            expected_meta_data = deepcopy(meta_data)
            expected_meta_data["system"] = {"foo": "bar"}
            expected_meta_data["update"]["start_ts"] = 10
            expected_meta_data["update"]["end_ts"] = 20
            expected_meta_data["update"]["duration"] = 10
            expected_meta_data["connected_realms"]["100"] = [
                {
                    "id": 100,
                    "name": "realm name 1",
                    "slug": "",
                    "category": "default",
                },
                {
                    "id": 101,
                    "name": "realm name 2",
                    "slug": "",
                    "category": "default",
                }
            ]
            expected_meta_data["connected_realms"]["200"] = [
                {
                    "id": 200,
                    "name": "realm name 1",
                    "slug": "",
                    "category": "seasonal",
                },
                {
                    "id": 201,
                    "name": "realm name 2",
                    "slug": "",
                    "category": "seasonal",
                }
            ]
            with open(meta_path, "r") as f:
                actual_meta_data = json.load(f)

            self.assertDictEqual(actual_meta_data, expected_meta_data)
