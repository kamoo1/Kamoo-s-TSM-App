from unittest import TestCase
from math import gcd
from copy import deepcopy

from ah.models import (
    MarketValueRecord,
    MarketValueRecords,
)
from ah.defs import SECONDS_IN


class TestModels(TestCase):
    def test_average_by_day(self):
        RECORDED_DAYS = 20
        RECORDS_PER_DAY = 4
        AVERAGE_WINDOW = 10
        records = MarketValueRecords()
        # 4 records per day
        record_list = [
            MarketValueRecord(
                timestamp=SECONDS_IN.DAY * (i / RECORDS_PER_DAY),
                market_value=100 * ((i + RECORDS_PER_DAY) // RECORDS_PER_DAY),
                num_auctions=100,
                min_buyout=1,
            )
            for i in range(RECORDED_DAYS * RECORDS_PER_DAY)
        ]
        for mvr in record_list:
            records.add(mvr, sort=False)

        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            AVERAGE_WINDOW,
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

        # reset records
        records.__root__ = []
        for mvr in record_list:
            records.add(mvr, sort=False)

        # compress first two days
        COMPRESSED_DAYS = 2
        ts_compressed = SECONDS_IN.DAY * COMPRESSED_DAYS
        n_removed = records.compress(ts_compressed, SECONDS_IN.DAY * COMPRESSED_DAYS)
        self.assertEqual(n_removed, COMPRESSED_DAYS * (RECORDS_PER_DAY - 1))
        self.assertEqual(
            len(records),
            (RECORDED_DAYS - COMPRESSED_DAYS) * RECORDS_PER_DAY + COMPRESSED_DAYS,
        )

        # average 20 days, inc. 2 compressed days
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            RECORDED_DAYS,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [100.0 * (i + 1) for i in range(RECORDED_DAYS)]
        self.assertEqual(avgs, avgs_expected)

        # average 20 days, inc. 2 compressed days
        # make sure the same when ts_compressed = 0
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            RECORDED_DAYS,
            ts_compressed=0,
        )
        avgs_expected = [100.0 * (i + 1) for i in range(RECORDED_DAYS)]
        self.assertEqual(avgs, avgs_expected)

        # average 10 days, inc. 2 compressed days
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 10
            SECONDS_IN.DAY * AVERAGE_WINDOW,
            AVERAGE_WINDOW,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [100.0 * (i + 1) for i in range(AVERAGE_WINDOW)]
        self.assertEqual(avgs, avgs_expected)

        # average 10 days, inc. 1 compressed days
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 11
            SECONDS_IN.DAY * (AVERAGE_WINDOW + 1),
            AVERAGE_WINDOW,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [100 + 100.0 * (i + 1) for i in range(AVERAGE_WINDOW)]
        self.assertEqual(avgs, avgs_expected)

        # average last 10 days, none of them are compressed
        # asking for mvrs
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            AVERAGE_WINDOW,
            return_mvr=True,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [1000.0 + 100.0 * (i + 1) for i in range(AVERAGE_WINDOW)]
        tss_expected = [
            # 10 days before + nth day + 0.5 day
            10 * SECONDS_IN.DAY + i * SECONDS_IN.DAY + 0.5 * SECONDS_IN.DAY
            for i in range(10)
        ]
        for avg, avg_expected, ts_expected in zip(avgs, avgs_expected, tss_expected):
            self.assertEqual(avg.market_value, avg_expected)
            self.assertEqual(avg.num_auctions, 100)
            self.assertEqual(avg.min_buyout, 1)
            self.assertEqual(avg.timestamp, ts_expected)

        # reset records
        records = MarketValueRecords()
        for mvr in record_list:
            records.add(mvr, sort=False)

        # expire 10 oldest records, then compress first 3 days
        COMPRESSED_DAYS = 3
        ts_compressed = SECONDS_IN.DAY * (COMPRESSED_DAYS + 10)
        n_removed = records.compress(ts_compressed, SECONDS_IN.DAY * COMPRESSED_DAYS)
        # make backup after compressing
        records_backup = deepcopy(records)
        self.assertEqual(
            # 10 days * 4 records per day + 3 days * 3 records per day
            n_removed,
            10 * RECORDS_PER_DAY + COMPRESSED_DAYS * (RECORDS_PER_DAY - 1),
        )
        self.assertEqual(
            len(records),
            # 3 days * 1 + 7 days * 4
            COMPRESSED_DAYS + 7 * RECORDS_PER_DAY,
        )

        # average 20 (10) days, inc. 3 compressed days, 7 days of 4 records per day.
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            RECORDED_DAYS,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [1000 + 100.0 * (i + 1) for i in range(10)]
        # first 10 days are None (expired)
        self.assertEqual(avgs[10:], avgs_expected)
        # same test settings for mvr
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 20
            SECONDS_IN.DAY * RECORDED_DAYS,
            RECORDED_DAYS,
            ts_compressed=ts_compressed,
            return_mvr=True,
        )
        for avg, avg_expected in zip(avgs[10:], avgs_expected):
            self.assertEqual(avg.market_value, avg_expected)
            self.assertEqual(avg.num_auctions, 100)
            self.assertEqual(avg.min_buyout, 1)

        # average 15 (5) days, inc. 3 compressed days, 2 days of 4 records per day.
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 15
            SECONDS_IN.DAY * 15,
            15,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [1000 + 100.0 * (i + 1) for i in range(5)]
        # first 10 days are None (expired)
        self.assertEqual(avgs[10:], avgs_expected)

        # make sure records doesn't get modified
        for a, b in zip(records, records_backup):
            # __eq__ only compares timestamp for total ordering
            # so we have to compare each field
            self.assertEqual(a.timestamp, b.timestamp)
            self.assertEqual(a.market_value, b.market_value)
            self.assertEqual(a.num_auctions, b.num_auctions)
            self.assertEqual(a.min_buyout, b.min_buyout)

    def test_average_by_day_staggered(self):
        RECORDED_DAYS = 20
        RECORDS_PER_DAY = 4
        records = MarketValueRecords()
        # 4 records per day
        record_list = [
            MarketValueRecord(
                timestamp=SECONDS_IN.DAY * (i / RECORDS_PER_DAY),
                market_value=100 * ((i + RECORDS_PER_DAY) // RECORDS_PER_DAY),
                num_auctions=100,
                min_buyout=1,
            )
            for i in range(RECORDED_DAYS * RECORDS_PER_DAY)
        ]
        for mvr in record_list:
            records.add(mvr, sort=False)

        # compress first 10 days
        COMPRESSED_DAYS = 10
        ts_compressed = SECONDS_IN.DAY * COMPRESSED_DAYS
        n_removed = records.compress(ts_compressed, SECONDS_IN.DAY * COMPRESSED_DAYS)
        self.assertEqual(n_removed, COMPRESSED_DAYS * (RECORDS_PER_DAY - 1))

        # average 10 days, inc. 5 compressed days
        # c=compressed records, r=not compressed records, `()` means to average
        # [c, c, c, c, (c, 2r), (2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r)]
        # c=[600, 700, 800, 900, 1000]
        # r=[1100(x4), 1200(x4), ..., 1500(x4), 1600(x2)]
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 15.5
            int(SECONDS_IN.DAY * 15.5),
            10,
            ts_compressed=ts_compressed,
        )
        part_compressed = [500.0 + 100.0 * (i + 1) for i in range(5)]
        part_compressed[-1] = int((part_compressed[-1] + 2 * 1100) / 3 + 0.5)
        part_not_compressed = [1050.0 + 100.0 * (i + 1) for i in range(5)]
        avgs_expected = list(map(int, [*part_compressed, *part_not_compressed]))
        self.assertEqual(avgs, avgs_expected)

        # average 15 days, inc. 10 compressed days
        # c=compressed records, r=not compressed records, `()` means to average
        # [c, ...(7 more c), c, (c, 2r), (2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r)]
        # c=[100, 200, ..., 900, 1000]
        # r=[1100(x4), 1200(x4), ..., 1500(x4), 1600(x2)]
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 15.5
            int(SECONDS_IN.DAY * 15.5),
            15,
            ts_compressed=ts_compressed,
        )
        part_compressed = [100.0 * (i + 1) for i in range(10)]
        part_compressed[-1] = int((part_compressed[-1] + 2 * 1100) / 3 + 0.5)
        part_not_compressed = [1050.0 + 100.0 * (i + 1) for i in range(5)]
        avgs_expected = list(map(int, [*part_compressed, *part_not_compressed]))
        self.assertEqual(avgs, avgs_expected)

        # average 5 days, inc. 0 compressed days
        # c=compressed records, r=not compressed records, `()` means to average
        # [(2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r)]
        # r=[1100(x4), 1200(x4), ..., 1500(x4), 1600(x2)]
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 15.5
            int(SECONDS_IN.DAY * 15.5),
            5,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [1050.0 + 100.0 * (i + 1) for i in range(5)]
        self.assertEqual(avgs, avgs_expected)

        # average 6 days, inc. 1 compressed day
        # c=compressed records, r=not compressed records, `()` means to average
        # [(c, 2r), (2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r), (2r, 2r)]
        # c=[1000]
        # r=[1100(x4), 1200(x4), ..., 1500(x4), 1600(x2)]
        avgs = MarketValueRecords.average_by_day(
            records,
            # now = day 15.5
            int(SECONDS_IN.DAY * 15.5),
            6,
            ts_compressed=ts_compressed,
        )
        avgs_expected = [1050.0 + 100.0 * (i + 1) for i in range(5)]
        avgs_expected = [int((1000 + 1100 * 2) / 3 + 0.5)] + avgs_expected
        self.assertEqual(avgs, avgs_expected)

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

        self.assertEqual(records.get_recent_market_value(9), 90)
        self.assertEqual(records.get_recent_num_auctions(9), 900)
        self.assertEqual(records.get_recent_min_buyout(9), 9000)

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
        self.assertEqual(records.get_historical_market_value(NOW), 0)

        records.empty()
        self.assertEqual(records.get_historical_market_value(NOW), 0)

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

        NOW = SECONDS_IN.DAY * (N_DAYS - 1) + 1
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

        records.remove_expired(6)
        self.assertEqual(len(records), 4)
        self.assertEqual(records[0].market_value, 60)

        records.remove_expired(9)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].market_value, 90)

        records.remove_expired(10)
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

    @classmethod
    def generate_records(
        cls,
        ts_now: int,
        ts_expires_in: int,
        n_expired: int = 10,
        n_recent: int = 10,
    ):
        """
        make series of records consisting of
        1. expired records
        2. records that will get compressed into n days
        3. recent records that will not get compressed

        compress
        """

        assert ts_now % SECONDS_IN.DAY >= n_recent
        records = MarketValueRecords()
        ts_end = ts_now - ts_now % SECONDS_IN.DAY
        # round up to day
        n_days = (ts_expires_in + SECONDS_IN.DAY - 1) // SECONDS_IN.DAY
        ts_start = ts_end - n_days * SECONDS_IN.DAY
        # anything before ts_start will be expired
        # anything after ts_end (recent records within a day) will not be compressed
        # how many records for each day in the compressed range
        n_records_per_day = 8
        n_compressed = n_days * n_records_per_day
        assert SECONDS_IN.DAY % n_records_per_day == 0

        # put expired records (ts_start - n_expired, ts_start)
        expired_records = [
            MarketValueRecord(
                timestamp=ts_start - n,
                market_value=1,
                num_auctions=1,
                min_buyout=1,
            )
            for n in range(n_expired, 0, -1)
        ]

        # put records that will be compressed (ts_start, ts_end)
        to_compressed_records = []
        expected_compressed_records = []
        last_compressed_num_auctions = 0
        last_compressed_market_value = 0
        last_day = -1
        for ts in range(ts_start, ts_end, SECONDS_IN.DAY // n_records_per_day):
            # range(0, n_days)
            n_th_day = (ts - ts_start) // SECONDS_IN.DAY
            # range(0, n_records_per_day)
            n_th_record = (ts % SECONDS_IN.DAY) // (SECONDS_IN.DAY // n_records_per_day)
            to_compressed_records.append(
                MarketValueRecord(
                    # compressed value would be the mid day timestamp of that day
                    # timestamp = ts_start + \
                    #   int(n_th_day * SECONDS_IN.DAY + SECONDS_IN.DAY // 2)
                    timestamp=ts,
                    # compressed value would be the average
                    # market_value = n_th_day * 100 + n_records_per_day / 2
                    market_value=100 * n_th_day + n_th_record,
                    # compressed value would be the average
                    # num_auctions = n_th_day * 10 + n_records_per_day / 2
                    num_auctions=10 * n_th_day + n_th_record,
                    # compressed value would be the min
                    # min_buyout = 0
                    min_buyout=1000 * n_th_day + n_th_record,
                )
            )

            # for generating edge record, it won't affect the compressed value
            # of num_auctions and market_value, but min_buyout will set to 0
            if n_th_day != last_day:
                last_day = n_th_day
                last_compressed_num_auctions = 10 * n_th_day + n_records_per_day / 2
                last_compressed_market_value = 100 * n_th_day + n_records_per_day / 2
                last_compressed_num_auctions = int(last_compressed_num_auctions + 0.5)
                last_compressed_market_value = int(last_compressed_market_value + 0.5)
                # calculate expected compressed records
                expected_compressed_records.append(
                    MarketValueRecord(
                        timestamp=ts_start
                        + int(n_th_day * SECONDS_IN.DAY + SECONDS_IN.DAY // 2),
                        market_value=last_compressed_market_value,
                        num_auctions=last_compressed_num_auctions,
                        min_buyout=1000 * n_th_day,
                    )
                )

        # we'd also like to add a edge case where the last record is
        # exactly ts_end - 1, to make sure we don't miss it
        edge_record = MarketValueRecord(
            timestamp=ts_end - 1,
            market_value=last_compressed_market_value,
            num_auctions=last_compressed_num_auctions,
            min_buyout=0,
        )
        expected_compressed_records[-1].min_buyout = 0

        # put records that will not be compressed (ts_end, ts_now)
        recent_records = [
            MarketValueRecord(
                timestamp=n,
                market_value=1,
                num_auctions=1,
                min_buyout=1,
            )
            for n in range(ts_end, ts_now, (ts_now - ts_end) // n_recent)
        ]
        if len(recent_records) > n_recent:
            # it's usually n_recent + 1
            recent_records = recent_records[:n_recent]

        expected_recent_records = [deepcopy(r) for r in recent_records]

        records = MarketValueRecords(
            __root__=[
                *expired_records,
                *to_compressed_records,
                edge_record,
                *recent_records,
            ]
        )

        return records, expected_compressed_records, expected_recent_records
