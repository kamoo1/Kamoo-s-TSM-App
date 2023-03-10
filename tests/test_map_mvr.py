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
)


class TestModels(TestCase):
    @classmethod
    def get_auction_param(cls, quantity, avg_price):
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

        group = [
            (avg_price + price_delta, n_sample_half),
            (avg_price - price_delta, n_sample_half),
        ]
        if should_append_avg_price:
            group.append((avg_price, 1))

        group.append((100 * avg_price, n_not_sample))

        return group, avg_price - price_delta

    @classmethod
    def mock_response(cls, type_, n_item, timestamp=None):
        expected = {}
        auctions = []
        auction_id = 0
        for i in range(n_item):
            item_id = i
            target_price = random.randint(1000, 4000)
            quantity = random.randint(21, 100)
            expected[item_id] = (target_price, quantity)
            group, min_price = cls.get_auction_param(quantity, target_price)
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
            resp = AuctionsResponse.parse_obj(obj)
        else:
            obj = {
                "_links": {},
                "auctions": auctions,
                "timestamp": timestamp,
            }
            resp = CommoditiesResponse.parse_obj(obj)

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
