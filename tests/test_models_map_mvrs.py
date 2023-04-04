from unittest import TestCase
from tests.test_models_mvrs import TestModels as TestModelsMVRs

from ah.models import (
    MarketValueRecords,
    MapItemStringMarketValueRecord,
    MapItemStringMarketValueRecords,
    MarketValueRecord,
    ItemString,
    ItemStringTypeEnum,
)
from ah.defs import SECONDS_IN


class TestModels(TestCase):
    def test_expired(self):
        db = MapItemStringMarketValueRecords()
        item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=1,
            bonuses=None,
            mods=None,
        )
        records = (
            MarketValueRecord(
                timestamp=i,
                market_value=100,
                num_auctions=100,
                min_buyout=1,
            )
            for i in range(10)
        )
        s_na_rec = 0
        s_na_ent = 0
        for mvr in records:
            na_rec, na_ent = db.add_market_value_record(item_string, mvr)
            s_na_rec += na_rec
            s_na_ent += na_ent
        self.assertEqual(s_na_rec, 10)
        self.assertEqual(s_na_ent, 1)
        NOW = 9
        # removes ts = 0, 1, 2
        nr_rec = db.remove_expired(3)
        self.assertEqual(nr_rec, 3)
        self.assertEqual(len(db[item_string]), 7)
        self.assertIn(item_string, db)

        nr_rec = db.remove_expired(11)
        nr_ent = db.remove_empty_entries()
        self.assertEqual(nr_ent, 1)
        self.assertEqual(nr_rec, 7)
        self.assertEqual(len(db), 0)
        self.assertNotIn(item_string, db)
        self.assertEqual(len(db[item_string]), 0)

    def test_sort(self):
        N_ITEMS = 10
        N_RECORDS_PER_ITEM = 10
        db = MapItemStringMarketValueRecords()
        s_na_rec, s_na_ent = 0, 0
        for i in range(N_ITEMS):
            item_string = ItemString(
                type=ItemStringTypeEnum.ITEM,
                id=i,
                bonuses=None,
                mods=None,
            )
            records = [
                MarketValueRecord(
                    timestamp=i,
                    market_value=100,
                    num_auctions=100,
                    min_buyout=1,
                )
                for i in range(N_RECORDS_PER_ITEM)
            ]
            # shuffle
            for mvr in (
                records[N_RECORDS_PER_ITEM // 2 :] + records[: N_RECORDS_PER_ITEM // 2]
            ):
                na_rec, na_ent = db.add_market_value_record(
                    item_string, mvr, sort=False
                )
                s_na_rec += na_rec
                s_na_ent += na_ent
        self.assertEqual(s_na_rec, N_RECORDS_PER_ITEM * N_ITEMS)
        self.assertEqual(s_na_ent, N_ITEMS)

        # assert not in order
        for records in db.values():
            temp = None
            ordered = True
            for i in range(N_RECORDS_PER_ITEM - 1):
                comp = records[i].timestamp < records[i + 1].timestamp
                if temp is None:
                    temp = comp
                elif temp != comp:
                    ordered = False
                    break
            self.assertFalse(ordered)

        # sort by timestamp, assert in order
        db.sort()
        for records in db.values():
            self.assertEqual(len(records), N_RECORDS_PER_ITEM)
            for i in range(N_RECORDS_PER_ITEM - 1):
                self.assertLess(records[i].timestamp, records[i + 1].timestamp)

        # shuffle again, only one item
        records = list(db.values())[0]
        records.__root__ = (
            records.__root__[N_RECORDS_PER_ITEM // 2 :]
            + records.__root__[: N_RECORDS_PER_ITEM // 2]
        )
        # assert not in order
        temp = None
        ordered = True
        for i in range(N_RECORDS_PER_ITEM - 1):
            comp = records[i].timestamp < records[i + 1].timestamp
            if temp is None:
                temp = comp
            elif temp != comp:
                ordered = False
                break
        self.assertFalse(ordered)

        # add one more record, sort by timestamp, assert in order
        record = MarketValueRecord(
            timestamp=100,
            market_value=100,
            num_auctions=100,
            min_buyout=1,
        )
        na_rec = records.add(record, sort=True)
        for i in range(len(records) - 1):
            self.assertLess(records[i].timestamp, records[i + 1].timestamp)

    def test_extend(self):
        db1 = MapItemStringMarketValueRecords()
        inc1 = MapItemStringMarketValueRecord(
            __root__={
                ItemString(
                    type=ItemStringTypeEnum.ITEM,
                    id=i,
                    bonuses=None,
                    mods=None,
                ): MarketValueRecord(
                    timestamp=1,
                    market_value=100,
                    num_auctions=100,
                    min_buyout=1,
                )
                for i in range(100)
            }
        )
        db1.update_increment(inc1)
        db2 = MapItemStringMarketValueRecords()
        inc2 = MapItemStringMarketValueRecord(
            __root__={
                ItemString(
                    type=ItemStringTypeEnum.ITEM,
                    id=i,
                    bonuses=None,
                    mods=None,
                ): MarketValueRecord(
                    timestamp=1,
                    market_value=100,
                    num_auctions=100,
                    min_buyout=1,
                )
                for i in range(50, 150)
            }
        )
        db2.update_increment(inc2)
        db1.extend(db2)

        for item_string, records in db1.items():
            if item_string.id < 50 or item_string.id >= 100:
                self.assertEqual(len(records), 1)
            else:
                self.assertEqual(len(records), 2)

        self.assertEqual(len(db1), 150)

    def test_update_increment(self):
        increment = MapItemStringMarketValueRecord(
            __root__={
                ItemString(
                    type=ItemStringTypeEnum.ITEM,
                    id=i,
                    bonuses=None,
                    mods=None,
                ): MarketValueRecord(
                    timestamp=1,
                    market_value=100,
                    num_auctions=100,
                    min_buyout=1,
                )
                for i in range(10)
            }
        )
        db = MapItemStringMarketValueRecords()
        na_rec, na_ent = db.update_increment(increment)
        self.assertEqual(na_rec, 10)
        self.assertEqual(na_ent, 10)
        self.assertEqual(len(db), 10)

        na_rec, na_ent = db.update_increment(increment)
        self.assertEqual(na_rec, 10)
        self.assertEqual(na_ent, 0)
        self.assertEqual(len(db), 10)
        for recs in db.values():
            self.assertEqual(len(recs), 2)

        new_item = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=100,
            bonuses=None,
            mods=None,
        )
        increment.__root__[new_item] = MarketValueRecord(
            timestamp=1,
            market_value=100,
            num_auctions=100,
            min_buyout=1,
        )
        na_rec, na_ent = db.update_increment(increment)
        self.assertEqual(na_rec, 11)
        self.assertEqual(na_ent, 1)
        self.assertEqual(len(db), 11)
        for item, recs in db.items():
            if item.id == 100:
                self.assertEqual(len(recs), 1)
            else:
                self.assertEqual(len(recs), 3)

    def test_query(self):
        increment = MapItemStringMarketValueRecord(
            __root__={
                ItemString(
                    type=ItemStringTypeEnum.ITEM,
                    id=i,
                    bonuses=(j,),
                    mods=None,
                ): MarketValueRecord(
                    timestamp=1,
                    market_value=100,
                    num_auctions=100,
                    min_buyout=1,
                )
                for i in range(10)
                for j in range(10)
            }
        )
        db = MapItemStringMarketValueRecords()
        db.update_increment(increment)
        for i in range(10):
            db_ = db.query(i)
            self.assertEqual(len(db_), 10)
            for item, recs in db_.items():
                self.assertEqual(item.id, i)
                self.assertEqual(len(recs), 1)

        # update all market_value in db_ to 200
        for recs in db_.values():
            for rec in recs:
                rec.market_value = 200

        # assert db is not affected
        for recs in db.values():
            for rec in recs:
                self.assertEqual(rec.market_value, 100)

    def assert_compression(
        self,
        records: MarketValueRecords,
        expected_compressed_records: MarketValueRecords,
        expected_recent_records: MarketValueRecords,
        ts_now: int,
    ):
        n_before = len(records)
        n_removed = records.compress(ts_now, ts_expires_in=SECONDS_IN.DAY * 60)
        n_after = len(records)
        self.assertEqual(n_before, n_after + n_removed)
        self.assertEqual(
            len(records),
            len(expected_compressed_records) + len(expected_recent_records),
        )
        for record, expected in zip(
            records, [*expected_compressed_records, *expected_recent_records]
        ):
            self.assertEqual(record.timestamp, expected.timestamp)
            self.assertEqual(record.market_value, expected.market_value)
            self.assertEqual(record.num_auctions, expected.num_auctions)
            self.assertEqual(record.min_buyout, expected.min_buyout)

        # compress again, make sure result is the same
        n_removed = records.compress(ts_now, ts_expires_in=SECONDS_IN.DAY * 60)
        self.assertEqual(n_removed, 0)
        self.assertEqual(
            len(records),
            len(expected_compressed_records) + len(expected_recent_records),
        )
        for record, expected in zip(
            records, [*expected_compressed_records, *expected_recent_records]
        ):
            self.assertEqual(record.timestamp, expected.timestamp)
            self.assertEqual(record.market_value, expected.market_value)
            self.assertEqual(record.num_auctions, expected.num_auctions)
            self.assertEqual(record.min_buyout, expected.min_buyout)

    def test_compression(self):
        db = MapItemStringMarketValueRecords()
        expected = {}
        for i in range(10):
            ts_now = 1680528498 + SECONDS_IN.DAY // 3
            (
                records,
                expected_compressed_records,
                expected_recent_records,
            ) = TestModelsMVRs.generate_records(ts_now, SECONDS_IN.DAY * 60)
            item_string = ItemString(
                type=ItemStringTypeEnum.PET,
                id=i,
                bonuses=None,
                mods=None,
            )
            db[item_string] = records
            expected[item_string] = (
                expected_compressed_records,
                expected_recent_records,
                ts_now,
            )

        for item_string, (
            expected_compressed_records,
            expected_recent_records,
            ts_now,
        ) in expected.items():
            self.assert_compression(
                db[item_string],
                expected_compressed_records,
                expected_recent_records,
                ts_now,
            )
