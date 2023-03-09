from collections import defaultdict
from typing import Tuple, Iterable

import numpy as np

from ah.defs import SECONDS_IN


class OnlineVariance:
    """
    Welford's algorithm computes the sample variance incrementally.
    """

    def __init__(self, iterable=None, ddof=1):
        self.ddof, self.n, self.mean, self.M2 = ddof, 0, 0.0, 0.0
        if iterable is not None:
            for datum in iterable:
                self.include(datum)

    def include(self, datum):
        self.n += 1
        self.delta = datum - self.mean
        self.mean += self.delta / self.n
        self.M2 += self.delta * (datum - self.mean)

    def exclude(self, datum):
        self.n -= 1
        self.delta = datum - self.mean
        self.mean -= self.delta / self.n
        self.M2 -= self.delta * (datum - self.mean)

    @property
    def variance(self):
        return self.M2 / (self.n - self.ddof)

    @property
    def std(self):
        return np.sqrt(self.variance)


def calc_rolling_avg(last_avg, curr_size, curr_v):
    return last_avg + (curr_v - last_avg) / curr_size


# def calc_market_values(item_n: int, prices: Generator[int, None, None]):
#     """market value calculation based off TradeSkillMaster's method
#     sources:
#     https://web.archive.org/web/20200609203103/https://support.tradeskillmaster.com/display/KB/AuctionDB+Market+Value
#     https://github.com/WouterBink/TradeSkillMaster-1/blob/master/TradeSkillMaster_AuctionDB/Modules/data.lua

#     """
#     MAX_JUMP_MUL = 1.2
#     MAX_STD_MUL = 1.5
#     SAMPLE_LO = 0.15
#     SAMPLE_HI = 0.3

#     #         lim0        lim1
#     #         |           |
#     # 0 1 2 3 4 5 6 7 8 9 10 11
#     # print()

#     if item_n == 0:
#         return None

#     last_price = 0
#     samples = []
#     ov = OnlineVariance()
#     lo, hi = int(item_n * SAMPLE_LO), int(item_n * SAMPLE_HI)
#     for price in prices:
#         if (
#             last_price
#             and ov.n >= lo
#             and (ov.n >= hi or price >= MAX_JUMP_MUL * last_price)
#         ):
#             break
#         last_price = price
#         samples.append(price)
#         ov.include(price)

#     if ov.n == item_n or ov.n == 1:
#         ov.ddof = 0

#     wstd = ov.std * MAX_STD_MUL
#     for dp in samples:
#         if abs(dp - ov.mean) > wstd:
#             ov.exclude(dp)

#     return ov.mean


class TSM_Math:
    """
    sources:
    https://web.archive.org/web/20200609203103/https://support.tradeskillmaster.com/display/KB/AuctionDB+Market+Value
    https://github.com/WouterBink/TradeSkillMaster-1/blob/master/TradeSkillMaster_AuctionDB/Modules/data.lua
    """

    DAY_WEIGHTS = [
        132,
        125,
        100,
        75,
        45,
        34,
        33,
        38,
        28,
        21,
        15,
        10,
        7,
        5,
        4,
    ]

    MAX_JUMP_MUL = 1.2
    MAX_STD_MUL = 1.5
    SAMPLE_LO = 0.15
    SAMPLE_HI = 0.3

    @classmethod
    def get_weighted_market_value(cls, timestamp_now: int) -> int:

        if not cls:
            # TODO: should we return 0?
            return 0

        size_days = len(cls.DAY_WEIGHTS)
        # 1. put market value snapshots into buckets of 1 day
        buckets = defaultdict(list)
        for snapshot in cls:
            i = (timestamp_now - snapshot.timestamp) // SECONDS_IN.DAY
            if i < size_days:
                buckets[i].append(snapshot.market_value)

        # 2. average each bucket so we get averaged market value for each day
        #    note that some buckets may be empty (None)
        days_average = [None] * size_days
        for i, snapshots in buckets.items():
            if snapshots:
                avg = sum(snapshots) / len(snapshots)
                days_average[i] = avg

        # 3. calculate weighted average over all buckets
        sum_market_value = 0
        sum_weights = 0
        for i, avg in enumerate(days_average):
            if avg is not None:
                sum_market_value += avg * cls.DAY_WEIGHTS[i]
                sum_weights += cls.DAY_WEIGHTS[i]

        return int(sum_market_value / sum_weights + 0.5) if sum_weights else 0

    @classmethod
    def calc_market_value(cls, item_n: int, price_groups: Iterable[Tuple[int, int]]):
        """calculate market value from a list of (price, quantity) tuples
        `price_groups` is a list of tuples of (price, quantity), sorted by price.
        a older version of this function used to take just a list of prices (by inflating
        `price_groups`) - albeit the intuitiveness, takes 10x more time to run.

        """

        #         lim0        lim1
        #         |           |
        # 0 1 2 3 4 5 6 7 8 9 10 11
        # print()
        if item_n == 0:
            return None

        lo, hi = int(item_n * cls.SAMPLE_LO), int(item_n * cls.SAMPLE_HI)
        samples = []
        samples_s = 0
        samples_n = 0
        last_sample = None
        # print()
        for price, price_quantity in price_groups:
            if (
                last_sample
                and samples_n >= lo
                and (samples_n >= hi or price >= cls.MAX_JUMP_MUL * last_sample[0])
            ):
                break

            samples.append([price, price_quantity])
            samples_n += price_quantity
            samples_s += price * price_quantity

            if samples_n > hi:
                off_by = samples_n - hi
                samples[-1][1] -= off_by
                samples_n -= off_by
                samples_s -= samples[-1][0] * off_by

                if samples[-1][1] == 0:
                    if last_sample:
                        samples.pop()
                    else:
                        samples[-1][1] = 1
                        samples_n += 1
                        samples_s += samples[-1][0]

                break

            last_sample = (price, price_quantity)

        # print(f"{samples=}, {samples_s=}, {samples_n=}")
        samples_mean = samples_s / samples_n
        samples_variance = 0
        for price, price_quantity in samples:
            samples_variance += (price - samples_mean) ** 2 * price_quantity
        ddof = 0 if samples_n == item_n else 1
        samples_std = (
            np.sqrt(samples_variance / (samples_n - ddof)) if samples_n > 1 else 0
        )
        samples_wstd = samples_std * cls.MAX_STD_MUL

        for price, price_quantity in samples:
            if np.abs(price - samples_mean) > samples_wstd:
                samples_s -= price * price_quantity
                samples_n -= price_quantity

        return samples_s / samples_n
