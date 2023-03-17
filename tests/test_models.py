from unittest import TestCase

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
    DBType,
)


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

        name = DBFileName(
            namespace=ns,
            db_type=DBType(type=DBTypeEnum.AUCTIONS, crid=123),
            ext=DBExtEnum.GZ,
        )
        expected = "dynamic-classic1x-us_auctions123.gz"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)
        self.assertTrue(name.is_compress())

        name = DBFileName(
            namespace=ns,
            db_type=DBTypeEnum.COMMODITIES,
            ext=DBExtEnum.BIN,
        )
        expected = "dynamic-classic1x-us_commodities.bin"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)
        self.assertFalse(name.is_compress())

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
            db_type=DBType(type=DBTypeEnum.META, crid=None),
            ext=DBExtEnum.JSON,
        )
        expected = "dynamic-classic1x-us_meta.json"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)

        # uses json by default for meta
        name = DBFileName(
            namespace=ns,
            db_type=DBType(type=DBTypeEnum.META),
        )
        expected = "dynamic-classic1x-us_meta.json"
        self.assertEqual(name.to_str(), expected)
        name_ = DBFileName.from_str(expected)
        self.assertTrue(name == name_)

        name = DBFileName(
            namespace=ns.to_str(),
            db_type="auctions123",
            ext="gz",
        )
        expected = "dynamic-classic1x-us_auctions123.gz"

        name = DBFileName(
            namespace=ns.to_str(),
            db_type="commodities",
            ext="bin",
        )
        expected = "dynamic-classic1x-us_commodities.bin"

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
                db_type=DBType(type=DBTypeEnum.COMMODITIES, crid=123),
                ext=DBExtEnum.GZ,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBType(type=DBTypeEnum.AUCTIONS, crid=None),
                ext=DBExtEnum.GZ,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBType(type=DBTypeEnum.AUCTIONS),
                ext=DBExtEnum.GZ,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBType(type=DBTypeEnum.AUCTIONS, crid=123),
                ext=DBExtEnum.JSON,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBType(type=DBTypeEnum.COMMODITIES),
                ext=DBExtEnum.JSON,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBType(type=DBTypeEnum.META),
                ext=DBExtEnum.BIN,
            )

        with self.assertRaises(ValueError):
            name = DBFileName(
                namespace=ns,
                db_type=DBType(type=DBTypeEnum.META, crid=123),
                ext=DBExtEnum.JSON,
            )

        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_auctions.bin")

        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_commodities123.bin")

        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_xxx123.gz")

        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_commodities.xxx")

        with self.assertRaises(ValueError):
            DBFileName.from_str("xxx-classic1x-us_auctions123.gz")

        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_meta.gz")

        with self.assertRaises(ValueError):
            DBFileName.from_str("dynamic-classic1x-us_meta.bin")
