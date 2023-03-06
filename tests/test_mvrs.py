from unittest import TestCase
import random
from math import gcd

from ah.models import (
    MapItemStringMarketValueRecords,
    MarketValueRecord,
    MarketValueRecords,
    ItemString,
    ItemStringTypeEnum,
    AuctionItem,
    CommodityItem,
)
from ah.defs import SECONDS_IN


class TestModels(TestCase):
    def test_average_by_day(self):
        RECORDED_DAYS = 20
        RECORDS_PER_DAY = 4
        AVERAGE_WINDOW = 10
        records = MarketValueRecords()
        # 4 records per day
        record_list = (
            MarketValueRecord(
                timestamp=SECONDS_IN.DAY * ((i + 1) / RECORDS_PER_DAY),
                market_value=100 * ((i + RECORDS_PER_DAY) // RECORDS_PER_DAY),
                num_auctions=100,
                min_buyout=1,
            )
            for i in range(RECORDED_DAYS * RECORDS_PER_DAY)
        )
        for mvr in record_list:
            records.add(mvr, sort=False)

        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            AVERAGE_WINDOW,
            is_records_sorted=True,
        )
        self.assertListEqual(
            avgs,
            [
                1100.0,
                1200.0,
                1300.0,
                1400.0,
                1500.0,
                1600.0,
                1700.0,
                1800.0,
                1900.0,
                2000.0,
            ],
        )

        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 10
            SECONDS_IN.DAY * AVERAGE_WINDOW,
            AVERAGE_WINDOW,
            is_records_sorted=True,
        )
        self.assertListEqual(
            avgs,
            [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0],
        )

        # remove records every other day, (we have 4 records per day)
        records.__root__ = [
            record for i, record in enumerate(records) if (i // 4) % 2 == 0
        ]
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            AVERAGE_WINDOW,
            is_records_sorted=True,
        )
        avgs_expected = [
            1100.0,
            None,
            1300.0,
            None,
            1500.0,
            None,
            1700.0,
            None,
            1900.0,
            None,
        ]
        self.assertListEqual(avgs, avgs_expected)

        # disrupt the order
        size = len(records)
        records.__root__ = records.__root__[size // 2 :] + records.__root__[: size // 2]
        avgs_false = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            AVERAGE_WINDOW,
            is_records_sorted=True,
        )
        self.assertNotEqual(avgs, avgs_false)

        avgs_true = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            AVERAGE_WINDOW,
            is_records_sorted=False,
        )
        self.assertListEqual(avgs, avgs_true)

    def test_sort(self):
        RECORDED_DAYS = 20
        RECORDS_PER_DAY = 4
        NOW = SECONDS_IN.DAY * RECORDED_DAYS
        records = MarketValueRecords()
        record_list = (
            MarketValueRecord(
                timestamp=SECONDS_IN.DAY * ((i + 1) / RECORDS_PER_DAY),
                market_value=100 * ((i + RECORDS_PER_DAY) // RECORDS_PER_DAY),
                num_auctions=100,
                min_buyout=1,
            )
            for i in range(RECORDED_DAYS * RECORDS_PER_DAY)
        )
        for mvr in record_list:
            records.add(mvr, sort=False)
        wmv = records.get_weighted_market_value(NOW)

        # disrupt the order
        size = len(records)
        records.__root__ = records.__root__[size // 2 :] + records.__root__[: size // 2]
        wmv_false = records.get_weighted_market_value(NOW)
        self.assertNotEqual(wmv, wmv_false)

        # sort
        records.sort()
        wmv_true = records.get_weighted_market_value(NOW)
        self.assertEqual(wmv, wmv_true)

    def test_recent(self):
        records = MarketValueRecords()
        record_list = (
            MarketValueRecord(
                timestamp=i,
                market_value=10 * i,
                num_auctions=100 * i,
                min_buyout=1000 * i,
            )
            for i in range(10)
        )
        for mvr in record_list:
            records.add(mvr, sort=False)

        self.assertEqual(records.get_recent_market_value(), 90)
        self.assertEqual(records.get_recent_num_auctions(), 900)
        self.assertEqual(records.get_recent_min_buyout(), 9000)

    def test_historical(self):
        # average mv of 60 days, first average by day then by 60 days
        N_DAYS = MarketValueRecords.HISTORICAL_DAYS
        daily_avg = list(range(1000, 1000 * N_DAYS + 1000, 1000))
        expected_historical = sum(daily_avg) / len(daily_avg)

        # 5 records per day
        N_RECORDS_PER_DAY = 5
        # days outside range
        N_SKIP_DAY = 2
        record_list = []
        for day_n, price_day in enumerate(daily_avg):
            # generate 4 records per day that averages to the price of the day
            records_of_day = (
                MarketValueRecord(
                    timestamp=10000
                    + (day_n + N_SKIP_DAY) * SECONDS_IN.DAY
                    + delta * 100,
                    market_value=price_day + delta * 100,
                    num_auctions=100,
                    min_buyout=10,
                )
                for delta in range(
                    -(N_RECORDS_PER_DAY // 2), N_RECORDS_PER_DAY // 2 + 1
                )
            )
            record_list.extend(records_of_day)

        # these records should not be used, it's outside the range
        records_pre = (
            MarketValueRecord(
                timestamp=i,
                market_value=10 * i,
                num_auctions=100 * i,
                min_buyout=1000 * i,
            )
            for i in range(10)
        )
        records = MarketValueRecords()
        for mvr in records_pre:
            records.add(mvr, sort=False)
        for mvr in record_list:
            records.add(mvr, sort=False)

        NOW = SECONDS_IN.DAY * (N_DAYS + N_SKIP_DAY)
        self.assertEqual(records.get_historical_market_value(NOW), expected_historical)

        # now fill only expired records
        records.empty()
        for mvr in records_pre:
            records.add(mvr, sort=False)
        self.assertEqual(records.get_historical_market_value(NOW), None)

        records.empty()
        self.assertEqual(records.get_historical_market_value(NOW), None)

    def test_weighted(self):
        weight_lcm = 1
        N_DAYS = len(MarketValueRecords.DAY_WEIGHTS)
        for w in MarketValueRecords.DAY_WEIGHTS:
            weight_lcm = weight_lcm * w // gcd(weight_lcm, w)

        prices = list(weight_lcm // w for w in MarketValueRecords.DAY_WEIGHTS)
        record_list = (
            MarketValueRecord(
                timestamp=i * SECONDS_IN.DAY,
                market_value=prices[i],
                num_auctions=100,
                min_buyout=10,
            )
            for i in range(N_DAYS)
        )
        records = MarketValueRecords()
        for mvr in record_list:
            records.add(mvr, sort=False)

        NOW = SECONDS_IN.DAY * (N_DAYS - 1)
        self.assertEqual(
            records.get_weighted_market_value(NOW),
            int(weight_lcm * N_DAYS / sum(MarketValueRecords.DAY_WEIGHTS) + 0.5),
        )

    def test_expired(self):
        records = MarketValueRecords()
        record_list = (
            MarketValueRecord(
                timestamp=i,
                market_value=10 * i,
                num_auctions=100 * i,
                min_buyout=1000 * i,
            )
            for i in range(10)
        )
        for mvr in record_list:
            records.add(mvr, sort=False)

        records.remove_expired(-100)
        self.assertEqual(len(records), 10)
        self.assertEqual(records[0].market_value, 0)

        records.remove_expired(5)
        self.assertEqual(len(records), 4)
        self.assertEqual(records[0].market_value, 60)

        records.remove_expired(8)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].market_value, 90)

        records.remove_expired(9)
        self.assertEqual(len(records), 0)

        record_list = (
            MarketValueRecord(
                timestamp=i,
                market_value=10 * i,
                num_auctions=100 * i,
                min_buyout=1000 * i,
            )
            for i in range(10)
        )
        for mvr in record_list:
            records.add(mvr, sort=False)

        records.remove_expired(100)
        self.assertEqual(len(records), 0)
