from unittest import TestCase
import random

from ah.models import (
    ItemString,
    ItemStringTypeEnum,
    AuctionItem,
)


class TestModels(TestCase):
    def test_item_string_hex(self):
        item_string1 = ItemString(
            type=ItemStringTypeEnum.ITEM, id=1, bonuses=(1, 2, 3), mods=(1, 1)
        )
        item_string2 = ItemString(
            type=ItemStringTypeEnum.ITEM, id=1, bonuses=(1, 2, 3), mods=(1, 1)
        )
        self.assertEqual(item_string1, item_string2)
        self.assertEqual(hash(item_string1), hash(item_string2))
        item_string2 = ItemString(
            type=ItemStringTypeEnum.ITEM, id=1, bonuses=(1, 3, 2), mods=(1, 1)
        )
        self.assertNotEqual(item_string1, item_string2)
        self.assertNotEqual(hash(item_string1), hash(item_string2))
        item_string2 = ItemString(
            type=ItemStringTypeEnum.PET, id=1, bonuses=(1, 2, 3), mods=(1, 2)
        )
        self.assertNotEqual(item_string1, item_string2)
        self.assertNotEqual(hash(item_string1), hash(item_string2))

    def test_item_string_to_str_1(self):
        # 9
        MOD_1 = ItemString.KEEPED_MODIFIERS_TYPES[0]
        MOD_1_V = 66
        # 29
        MOD_2 = ItemString.KEEPED_MODIFIERS_TYPES[1]
        MOD_2_V = 77

        BONUSES = (1, 2, 3)
        BONUSES_STR = ":".join(map(str, BONUSES))
        BONUSES_LEN = len(BONUSES)

        self.assertLess(MOD_1, MOD_2)

        item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=1,
            bonuses=BONUSES,
            mods=(MOD_1, MOD_1_V, MOD_2, MOD_2_V),
        )
        self.assertEqual(
            str(item_string),
            f"i:1::{BONUSES_LEN}:{BONUSES_STR}:2:{MOD_1}:{MOD_1_V}:{MOD_2}:{MOD_2_V}",
        )

    def test_item_string_to_str_2(self):
        item_string = ItemString(
            type=ItemStringTypeEnum.PET,
            id=123,
            bonuses=(),
            mods=(),
        )
        self.assertEqual(item_string.to_str(), "p:123")

    def test_item_string_to_str_3(self):
        item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=1,
            bonuses=(),
            mods=(),
        )
        self.assertEqual(
            item_string.to_str(),
            "1",
        )

        item_string = ItemString(
            type=ItemStringTypeEnum.PET,
            id=1,
            bonuses=(),
            mods=(),
        )
        self.assertEqual(
            item_string.to_str(),
            "p:1",
        )

        item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=1,
            bonuses=(1, 2, 3),
            mods=(),
        )
        self.assertEqual(
            item_string.to_str(),
            "i:1::3:1:2:3",
        )

        item_string = ItemString(
            type=ItemStringTypeEnum.ITEM,
            id=1,
            bonuses=(),
            mods=(1, 1, 2, 2),
        )
        self.assertEqual(
            item_string.to_str(),
            "i:1::0:2:1:1:2:2",
        )

    @classmethod
    def mock_bonuses(cls):
        # some random number that might get filtered
        rnd_any = [random.randint(1, 10000) for _ in range(20)]
        # plus some actual bonuses that should not get filtered
        rnd_bonuses = random.sample(list(ItemString.MAP_BONUSES.keys()), 20)
        in_bonuses = list(set(rnd_bonuses + rnd_any))
        # filter out bonuses that have ilvl fields
        in_bonuses = [
            bonus_id
            for bonus_id in in_bonuses
            if not ItemString.SET_BONUS_ILVL_FIELDS
            & set(ItemString.MAP_BONUSES.get(bonus_id, {}).keys())
        ]
        random.shuffle(in_bonuses)

        out_bonuses = filter(ItemString.MAP_BONUSES.__contains__, in_bonuses)
        out_bonuses = sorted(out_bonuses)
        return tuple(in_bonuses), tuple(out_bonuses)

    def mock_modifiers(self):
        k = range(1, 100)
        keys = set(random.sample(k, 5))
        keys |= set(ItemString.KEEPED_MODIFIERS_TYPES)

        raw = [{"type": key, "value": random.randint(1, 100)} for key in keys]
        random.shuffle(raw)

        srt = []
        tmp = {o["type"]: o["value"] for o in raw}
        for k in sorted(tmp.keys()):
            if k not in ItemString.KEEPED_MODIFIERS_TYPES:
                continue
            srt.append(k)
            srt.append(tmp[k])
        return raw, srt

    def test_item_string_from_item(self):
        """Test sort and filter behavior for bonuses and modifiers"""
        bonus_in, bonus_out = self.mock_bonuses()
        modifiers_in, modifiers_out = self.mock_modifiers()
        item = AuctionItem(
            id=1000,
            context=0,
            bonus_lists=bonus_in,
            modifiers=modifiers_in,
        )
        item_string = ItemString.from_item(item)
        self.assertEqual(item_string.type, ItemStringTypeEnum.ITEM)
        self.assertEqual(item_string.id, item.id)
        self.assertEqual(item_string.bonuses, tuple(bonus_out))
        self.assertEqual(item_string.mods, tuple(modifiers_out))

        bonus_in, bonus_out = self.mock_bonuses()
        modifiers_in, modifiers_out = self.mock_modifiers()
        item = AuctionItem(
            id=1000,
            context=0,
            bonus_lists=bonus_in,
            modifiers=modifiers_in,
            pet_breed_id=11,
            pet_level=12,
            pet_quality_id=13,
            pet_species_id=14,
        )
        item_string = ItemString.from_item(item)
        self.assertEqual(item_string.type, ItemStringTypeEnum.PET)
        self.assertEqual(item_string.id, item.pet_species_id)
        # pets don't take bonuses & modifiers
        self.assertEqual(item_string.bonuses, None)
        self.assertEqual(item_string.mods, None)
        self.assertEqual(item_string.to_str(), f"p:{item_string.id}")

    def test_item_level(self):
        bonuses, mods = [8851, 8852, 8801], [
            {"type": 28, "value": 2164},
            {"type": 29, "value": 36},
            {"type": 30, "value": 49},
            {"type": 38, "value": 7},
            {"type": 39, "value": 47988},
            {"type": 40, "value": 856},
            {"type": 42, "value": 48},
        ]
        ret = "i:201937::i337"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=201937,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [6655, 1707], [
            {"type": 9, "value": 30},
            {"type": 28, "value": 1079},
        ]
        ret = "i:25291::i66"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=25291,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [7969, 6652, 1679], [
            {"type": 9, "value": 70},
            {"type": 28, "value": 2524},
        ]
        ret = "i:199038::i302"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=199038,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [7968, 6652, 7937, 1687], [
            {"type": 9, "value": 70},
            {"type": 28, "value": 2475},
        ]
        ret = "i:198996::i292"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=198996,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [6654, 1692], [
            {"type": 9, "value": 58},
            {"type": 28, "value": 1888},
        ]
        ret = "i:24955::i158"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=24955,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [596, 601, 689, 1679, 3408], None
        ret = "i:126997::-4"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=126997,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [669, 600, 689, 1712, 3408], None
        ret = "i:126996::+3"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=126996,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [6716, 8156, 1487], [{"type": 28, "value": 2142}]
        ret = "i:172319::+15"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=172319,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)

        bonuses, mods = [1700, 4928], [{"type": 28, "value": 708}]
        ret = "i:152837::+10"
        i = ItemString.from_auction_item(
            AuctionItem(
                id=152837,
                context=0,
                bonus_lists=bonuses,
                modifiers=mods,
            )
        )
        self.assertEqual(i.to_str(), ret)
