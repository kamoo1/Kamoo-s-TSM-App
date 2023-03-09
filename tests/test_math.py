from unittest import TestCase
from ah.math import TSM_Math, OnlineVariance


class TestMarketValue(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.temp_dir = None

    def test_market_value_calc_official_1(self):
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
        expected = 14.5
        actual = TSM_Math.calc_market_value(24, price_groups)
        self.assertAlmostEqual(expected, actual)

    def test_market_value_calc_official_2(self):
        # viration of official test case from TradeSkillMaster website
        price_groups = [
            (5, 1),
            (13, 2),
            (15, 3),
            (16, 7),
            (17, 2),
            (19, 1),
            (21, 2),
            (29, 1),
            (45, 2),
            (46, 1),
            (47, 1),
            (100, 1),
        ]
        expected = 14.5
        actual = TSM_Math.calc_market_value(24, price_groups)
        self.assertAlmostEqual(expected, actual)

    def test_market_value_calc_edge_1(self):
        price_groups = [(1, 1), (1.1, 6)]
        expected = 1.05
        actual = TSM_Math.calc_market_value(7, price_groups)
        self.assertAlmostEqual(expected, actual)

    def test_market_value_calc_edge_2(self):
        price_groups = [(4, 1), (4.7, 1)]
        expected = 4
        actual = TSM_Math.calc_market_value(2, price_groups)
        self.assertAlmostEqual(expected, actual)

    def test_market_value_calc_edge_3(self):
        price_groups = [(10, 1), (100, 1)]
        expected = 10
        actual = TSM_Math.calc_market_value(2, price_groups)
        self.assertAlmostEqual(expected, actual)

    def test_market_value_calc_edge_4(self):
        price_groups = [(4, 1)]
        expected = 4
        actual = TSM_Math.calc_market_value(1, price_groups)
        self.assertAlmostEqual(expected, actual)

    def test_market_value_calc_edge_5(self):
        price_groups = [(1, 1), (2, 6)]
        # jump limit excessed
        expected = 1
        actual = TSM_Math.calc_market_value(7, price_groups)
        self.assertAlmostEqual(expected, actual)

    def test_online_variance(self):
        ov = OnlineVariance()
        ov.include(0)
        history = {i: (ov.mean, ov.std) for i in range(1, 101) if ov.include(i) is None}
        for i in range(100, 1, -1):
            ov.exclude(i)
            self.assertEqual(history[i - 1], (ov.mean, ov.std))
