from unittest import TestCase
import random

from ah.models import (
    MapItemStringMarketValueRecord,
    AuctionItem,
    CommodityItem,
    AuctionsResponse,
    CommoditiesResponse,
    Auction,
    Commodity,
    GameVersionEnum,
    ItemString,
    ItemStringTypeEnum,
)


class TestModels(TestCase):
    @classmethod
    def get_auction_param(
        cls, quantity, avg_price, game_version=GameVersionEnum.RETAIL
    ):
        """
        generate a group of item that their average price is avg_price

        for example if n_item = 10 and avg_price = 100
        then one of the valid output is:
        [
            (110, 5),
            (90, 5),
        ]
        """
        assert avg_price > 20
        # !!!
        assert quantity > 20

        n_sample = int(MapItemStringMarketValueRecord.SAMPLE_HI * quantity)
        n_not_sample = quantity - n_sample
        # print(n_sample, n_not_sample)
        if n_sample % 2 == 1:
            should_append_avg_price = True
        else:
            should_append_avg_price = False

        n_sample_half = n_sample // 2
        price_delta = avg_price * (
            (MapItemStringMarketValueRecord.MAX_JUMP_MUL - 1) // 2
        )

        # we generate n_half item with price avg_price + price_delta
        # and n_half item with price avg_price - price_delta

        if game_version in (GameVersionEnum.CLASSIC, GameVersionEnum.CLASSIC_WLK):
            group = [
                ((avg_price + price_delta) * n_sample_half, n_sample_half),
                ((avg_price - price_delta) * n_sample_half, n_sample_half),
            ]
            if should_append_avg_price:
                group.append((avg_price, 1))
            group.append((100 * avg_price * n_not_sample, n_not_sample))
        else:
            group = [
                (avg_price + price_delta, n_sample_half),
                (avg_price - price_delta, n_sample_half),
            ]
            if should_append_avg_price:
                group.append((avg_price, 1))
            group.append((100 * avg_price, n_not_sample))

        return group, avg_price - price_delta

    @classmethod
    def mock_response(
        cls, type_, n_item, timestamp=None, game_version=GameVersionEnum.RETAIL
    ):
        expected = {}
        auctions = []
        auction_id = 0
        for i in range(n_item):
            item_id = i
            target_price = random.randint(1000, 4000)
            quantity = random.randint(21, 100)
            expected[item_id] = (target_price, quantity)
            group, min_price = cls.get_auction_param(
                quantity, target_price, game_version=game_version
            )
            # print(group)
            for price, quantity in group:
                if type_ == "auction":
                    auction = Auction(
                        id=auction_id,
                        item=AuctionItem(
                            id=item_id,
                            context=1,
                            bonus_lists=None,
                            modifiers=None,
                        ),
                        buyout=price,
                        quantity=quantity,
                        time_left="VERY_LONG",
                    )
                else:
                    auction = Commodity(
                        id=auction_id,
                        item=CommodityItem(id=item_id),
                        unit_price=price,
                        quantity=quantity,
                        time_left="VERY_LONG",
                    )
                auction_id += 1
                auctions.append(auction)

        random.shuffle(auctions)

        if type_ == "auction":
            obj = {
                "_links": {},
                "connected_realm": {},
                "auctions": auctions,
                "commodities": {},
                "timestamp": timestamp,
            }
            resp = AuctionsResponse.model_validate(obj)
        else:
            obj = {
                "_links": {},
                "auctions": auctions,
                "timestamp": timestamp,
            }
            resp = CommoditiesResponse.model_validate(obj)

        return resp, expected, min_price

    def test_increment(self):
        timestamp = 1000
        resp, expected, min_price = self.mock_response(
            "auction", 1, timestamp=timestamp
        )
        increment = MapItemStringMarketValueRecord.from_response(resp)
        for item_string, record in increment.items():
            item_id = item_string.id
            self.assertEqual(record.market_value, expected[item_id][0])
            self.assertEqual(record.num_auctions, expected[item_id][1])
            self.assertEqual(record.min_buyout, min_price)

        resp, expected, min_price = self.mock_response(
            "commodity", 1, timestamp=timestamp
        )
        increment = MapItemStringMarketValueRecord.from_response(resp)
        for item_string, record in increment.items():
            item_id = item_string.id
            self.assertEqual(record.market_value, expected[item_id][0])
            self.assertEqual(record.num_auctions, expected[item_id][1])
            self.assertEqual(record.min_buyout, min_price)

    def test_increment_classic(self):
        """classic auction response's "buyout" and "bid" are total price."""
        timestamp = 1000
        resp, expected, min_price = self.mock_response(
            "auction", 1, timestamp=timestamp, game_version=GameVersionEnum.CLASSIC
        )
        increment = MapItemStringMarketValueRecord.from_response(
            resp, game_version=GameVersionEnum.CLASSIC
        )
        for item_string, record in increment.items():
            item_id = item_string.id
            self.assertEqual(record.market_value, expected[item_id][0])
            self.assertEqual(record.num_auctions, expected[item_id][1])
            self.assertEqual(record.min_buyout, min_price)

        resp, expected, min_price = self.mock_response(
            "commodity", 1, timestamp=timestamp
        )
        increment = MapItemStringMarketValueRecord.from_response(resp)
        for item_string, record in increment.items():
            item_id = item_string.id
            self.assertEqual(record.market_value, expected[item_id][0])
            self.assertEqual(record.num_auctions, expected[item_id][1])
            self.assertEqual(record.min_buyout, min_price)

    def test_edge(self):
        obj = {
            "_links": {},
            "connected_realm": {},
            "commodities": {},
            "timestamp": 100,
        }
        resp = AuctionsResponse.model_validate(obj)
        self.assertEqual(resp.get_auctions(), [])

        obj = {
            "_links": {},
            "timestamp": 100,
        }
        resp = CommoditiesResponse.model_validate(obj)
        self.assertEqual(resp.get_auctions(), [])

    def test_min_price_classic(self):
        """classic auction has buyout=0 for bid-only auctions"""
        obj = {
            "_links": {},
            "connected_realm": {},
            "auctions": [
                Auction(
                    id=0,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    buyout=0,
                    bid=100,
                    quantity=10,
                    time_left="VERY_LONG",
                ),
                Auction(
                    id=1,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    buyout=555,
                    bid=100,
                    quantity=5,
                    time_left="VERY_LONG",
                ),
            ],
            "commodities": {},
            "timestamp": 100,
        }
        resp = AuctionsResponse.model_validate(obj)
        increment = MapItemStringMarketValueRecord.from_response(
            resp, game_version=GameVersionEnum.CLASSIC
        )
        itemstring = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=0,
            bonuses=None,
            mods=None,
        )
        # buyout / quantity
        self.assertEqual(increment[itemstring].min_buyout, 111)

        """second case, all bid-only auctions
        """
        obj = {
            "_links": {},
            "connected_realm": {},
            "auctions": [
                Auction(
                    id=0,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    buyout=0,
                    bid=100,
                    quantity=10,
                    time_left="VERY_LONG",
                ),
                Auction(
                    id=1,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    buyout=0,
                    bid=100,
                    quantity=5,
                    time_left="VERY_LONG",
                ),
            ],
            "commodities": {},
            "timestamp": 100,
        }
        resp = AuctionsResponse.model_validate(obj)
        increment = MapItemStringMarketValueRecord.from_response(
            resp, game_version=GameVersionEnum.CLASSIC
        )
        itemstring = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=0,
            bonuses=None,
            mods=None,
        )
        self.assertEqual(increment[itemstring].min_buyout, 0)

    def test_min_price_retail(self):
        """retail auction doesn't have buyout field for bid-only auctions"""
        obj = {
            "_links": {},
            "connected_realm": {},
            "auctions": [
                Auction(
                    id=0,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    bid=100,
                    quantity=10,
                    time_left="VERY_LONG",
                ),
                Auction(
                    id=1,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    buyout=555,
                    bid=100,
                    quantity=5,
                    time_left="VERY_LONG",
                ),
            ],
            "commodities": {},
            "timestamp": 100,
        }
        resp = AuctionsResponse.model_validate(obj)
        increment = MapItemStringMarketValueRecord.from_response(
            resp, game_version=GameVersionEnum.RETAIL
        )
        itemstring = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=0,
            bonuses=None,
            mods=None,
        )
        # buyout don't have to be divided by quantity
        self.assertEqual(increment[itemstring].min_buyout, 555)

        """second case, all bid-only auctions
        """
        obj = {
            "_links": {},
            "connected_realm": {},
            "auctions": [
                Auction(
                    id=0,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    bid=100,
                    quantity=10,
                    time_left="VERY_LONG",
                ),
                Auction(
                    id=1,
                    item=AuctionItem(
                        id=0,
                        context=1,
                        bonus_lists=None,
                        modifiers=None,
                    ),
                    bid=100,
                    quantity=5,
                    time_left="VERY_LONG",
                ),
            ],
            "commodities": {},
            "timestamp": 100,
        }
        resp = AuctionsResponse.model_validate(obj)
        increment = MapItemStringMarketValueRecord.from_response(
            resp, game_version=GameVersionEnum.RETAIL
        )
        itemstring = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=0,
            bonuses=None,
            mods=None,
        )
        self.assertEqual(increment[itemstring].min_buyout, 0)
