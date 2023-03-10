from unittest import TestCase
import random

from ah.models import (
    MapItemStringMarketValueRecord,
    MapItemStringMarketValueRecords,
    MarketValueRecord,
    MarketValueRecords,
    ItemString,
    ItemStringTypeEnum,
    AuctionItem,
    CommodityItem,
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
        self.assertEqual(item_string.to_str(), f"p:123")

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
        l = range(1, 100)
        raw = random.sample(l, 5)
        srt = sorted(raw)
        return raw, srt

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
