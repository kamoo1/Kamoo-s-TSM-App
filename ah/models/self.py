from functools import partial
from enum import Enum
from heapq import heappush, heappop
from collections import defaultdict
from functools import total_ordering, wraps
from typing import List, Dict, ClassVar, Generator, Tuple, Optional, Union, Callable

from pydantic import Field, validator

from ah.protobuf.item_db_pb2 import (
    ItemDB,
    ItemString as ItemStringPB,
    ItemStringType as ItemStringTypePB,
)
from ah.storage import BinaryFile
from ah.models.base import _BaseModel, _BaseModelRootDictMixin, _BaseModelRootListMixin
from ah.models.blizzard import (
    GenericAuctionsResponseInterface,
    GenericItemInterface,
    AuctionItem,
    CommodityItem,
)
from ah.defs import SECONDS_IN
from ah.math import TSM_Math

__all__ = (
    "MarketValueRecord",
    "MarketValueRecords",
    "MapItemStringMarketValueRecords",
    "MapItemStringMarketValueRecord",
    "ItemString",
    "ItemStringTypeEnum",
)

"""
# This is a rough representation of the old TSM's data structure,
# note that it will not be implemented in the same way.

data = {
    "item_string": {
        "records" : {
            ...,
            # only has mv avg if not today
            "day - 1": 1000,
            # rolling average
            "day": {"market_value_avg": 1000, "n_scan": 2}
        },
        "last_record": ...,
        "min_buyout": ...,
        # 14 day weighted mv
        "market_value": ...,
    },
    ...
}
"""


@total_ordering
class MarketValueRecord(_BaseModel):
    """

    >>> market_value_record = {
            # update timestamp
            "timestamp": 1234567890,
            # market value, might be None
            "market_value": 10000,
            # number of auctions
            "num_auctions": 100,
            # min buyout, might be None
            "min_buyout": 1000,
        }
    """

    timestamp: int
    # required optional field, if there's no auctions, this field is None
    market_value: Optional[int] = ...
    num_auctions: int
    min_buyout: Optional[int] = None

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp


class MarketValueRecords(_BaseModelRootListMixin[MarketValueRecord], _BaseModel):

    # TODO: figure out if we want to return 0 and update the return type,
    #       maybe add warning logs when there are no records.
    """
    Holds an list of MarketValueRecord, ordered by timestamp in ascending order.

    >>> market_value_records = [
            $market_value_record,
            ...
        ]
    """

    __root__: List[MarketValueRecord] = Field(default_factory=list)
    DAY_WEIGHTS: ClassVar[int] = [
        4,
        5,
        7,
        10,
        15,
        21,
        28,
        38,
        33,
        34,
        45,
        75,
        100,
        125,
        132,
    ]
    HISTORICAL_DAYS: ClassVar[int] = 60

    def add(self, market_value_record: MarketValueRecord, sort: bool = False) -> int:
        # TODO: go over all methods having `sort` parameter, making sure it
        # doesn't do extra work. (for example, for `ItemStringMarketValueRecords`,
        # we don't have to sort all records, just the ones that are added)
        self.append(market_value_record)
        if sort:
            self.sort()

        return 1

    def empty(self):
        self.__root__ = []

    def remove_expired(self, ts_expires: int) -> int:
        for i in range(len(self) + 1):
            if i == len(self) or self[i].timestamp > ts_expires:
                break

        self.__root__ = self[i:]
        return i

    def get_recent_num_auctions(self, ts_last_update_begin: int) -> int:
        # return newest record
        # TODO: check that records without any auctions (None marketvalue) are added,
        # because sometimes there are no auctions for an item
        if (
            self
            and self[-1].timestamp >= ts_last_update_begin
            and self[-1].num_auctions
        ):
            return self[-1].num_auctions
        else:
            return 0

    def get_recent_min_buyout(self, ts_last_update_begin: int) -> int:
        if self and self[-1].timestamp >= ts_last_update_begin and self[-1].min_buyout:
            return self[-1].min_buyout
        else:
            return 0

    def get_recent_market_value(self, ts_last_update_begin) -> int:
        if (
            self
            and self[-1].timestamp >= ts_last_update_begin
            and self[-1].market_value
        ):
            return self[-1].market_value
        else:
            return 0

    @classmethod
    def average_by_day(
        cls,
        records: "MarketValueRecords",
        ts_now: int,
        n_days_before: int,
        is_records_sorted: bool = True,
    ) -> List[Union[float, None]]:
        """
        note that records should be passed in ascending order
        """
        # 1. put market value snapshots into buckets of 1 day
        buckets = defaultdict(list)
        for record in reversed(records):
            if record.market_value is None:
                continue
            i = (ts_now - record.timestamp) // SECONDS_IN.DAY
            if i < 0:
                continue

            elif i < n_days_before:
                buckets[i].append(record.market_value)

            elif is_records_sorted:
                # if records are sorted in descending order, we can stop
                # processing them when we reach the first record that is
                # older than `n_days_before`
                break

        # 2. average each bucket so we get averaged market value for each day
        #    note that some buckets may be empty, indicated by `None` instead
        #    of an average.
        days_average = [None] * n_days_before
        for i, market_values in buckets.items():
            if market_values:
                avg = sum(market_values) / len(market_values)
                days_average[n_days_before - i - 1] = avg

        return days_average

    def get_historical_market_value(self, ts_now: int) -> int:
        # TSM says it's a 60-day average of "weighted market value", I'm just
        # getting lazy here using average of records instead.

        # To take uneven updates per day into account, we'd first get the average
        # market values for each day, for a total of 60 days, and then calculate
        # the average of those 60 days.

        if not self:
            self._logger.warning(
                f"{self}: no records, get_historical_market_value() returns None"
            )
            return None

        days_average = self.average_by_day(
            self, ts_now, self.HISTORICAL_DAYS, is_records_sorted=True
        )
        # calculate average of all buckets that are not None
        sum_market_value = 0
        n_days = 0
        for avg in days_average:
            if avg is not None:
                sum_market_value += avg
                n_days += 1

        if n_days == 0:
            self._logger.warning(
                f"{self}: all records expired, get_historical_market_value() returns "
                f"{TSM_EMPTY_VALUES.MARKET_VALUE}"
            )
            return TSM_EMPTY_VALUES.MARKET_VALUE

        return int(sum_market_value / n_days + 0.5)

    def get_weighted_market_value(self, ts_now: int) -> int:
        if not self:
            self._logger.warning(
                f"{self}: no records, get_weighted_market_value() returns "
                f"{TSM_EMPTY_VALUES.MARKET_VALUE}"
            )
            return TSM_EMPTY_VALUES.MARKET_VALUE

        days_average = self.average_by_day(
            self, ts_now, len(self.DAY_WEIGHTS), is_records_sorted=True
        )
        # calculate weighted average over all buckets that are not None
        sum_market_value = 0
        sum_weights = 0
        for i, avg in enumerate(days_average):
            if avg is not None:
                sum_market_value += avg * self.DAY_WEIGHTS[i]
                sum_weights += self.DAY_WEIGHTS[i]

        # should return 0 according to TSM
        # https://github.com/WouterBink/TradeSkillMaster-1/blob/master/TradeSkillMaster_AuctionDB/Modules/data.lua#L115
        if sum_weights:
            return int(sum_market_value / sum_weights + 0.5)
        else:
            self._logger.warning(
                f"{self}: all records expired, get_weighted_market_value() returns "
                f"{TSM_EMPTY_VALUES.MARKET_VALUE}"
            )
            return TSM_EMPTY_VALUES.MARKET_VALUE


# def bound_cache(func: Callable) -> Callable:
#     """
#     Cache the result of a object's method call,
#     there's shouldn't be any arguments passed to the method.

#     """

#     # we can't really put cache in the object because of pydantic won't allow it
#     # if only pydantic has it's own cache implementation for frozen models...
#     cache = {}

#     @wraps(func)
#     def wrapper(that, *args, **kwargs):
#         # check no arguments passed
#         if args or kwargs:
#             raise ValueError("method should not have any arguments")

#         key = (id(that), func.__name__)
#         if key in cache:
#             return cache[key]

#         result = func(that)
#         cache[key] = result
#         return result

#     return wrapper


class ItemStringTypeEnum(str, Enum):
    PET = "p"
    ITEM = "i"


class ItemString(_BaseModel):
    """This is a frozen model, it has a __hash__ method generated by pydantic
    that calcueates the hash value from the model's immutable fields.

    To instantiating this model in anyway other than `from_item` (not recommended):
    - Sort the `mods` fields, `mods` is an tuple (i, i+1, ...)
      transformed from a dict where `i` is the key and `i+1` is `i`'s value.
      the dict is sorted by key in ascending order.

    - Filter the `mods` field, only keep the key-value pairs where the key is
      in `KEEPED_MODIFIERS_TYPES`.

    - Sort the `bonuses` field, `bonuses` is a tuple of ints.

    - Pets don't have `mods` or `bonuses` fields, they take `breed_id` from
      `AuctionItem` as their `id` field.
    """

    type: str
    id: int
    bonuses: Optional[Tuple[int, ...]] = Field(...)
    # used to be kv pairs, cast to even-length tuple for easy hashing
    mods: Optional[Tuple[int, ...]] = Field(...)

    KEEPED_MODIFIERS_TYPES: ClassVar[List[int]] = [9, 29, 30]

    @classmethod
    def from_item(cls, item: GenericItemInterface) -> str:
        if isinstance(item, AuctionItem):
            return cls.from_auction_item(item)
        elif isinstance(item, CommodityItem):
            return cls.from_commodity_item(item)
        else:
            raise TypeError(f"unknown item type: {type(item)}")

    @classmethod
    def from_auction_item(cls, item: AuctionItem) -> "ItemString":
        if item.pet_breed_id is not None:
            return cls(
                type=ItemStringTypeEnum.PET,
                id=item.pet_breed_id,
                bonuses=None,
                mods=None,
            )

        else:
            if item.bonus_lists:
                # TODO: confirm there's no filtering for bonus list in TSM
                bonuses = sorted(item.bonus_lists)

            else:
                bonuses = None

            heap = []
            if item.modifiers:
                for mod in item.modifiers:
                    mod_type = mod["type"]
                    mod_value = mod["value"]
                    if mod_type not in cls.KEEPED_MODIFIERS_TYPES:
                        continue
                    heappush(heap, (mod_type, mod_value))
                mods = []
                while heap:
                    mod_type, mod_value = heappop(heap)
                    mods.append(mod_type)
                    mods.append(mod_value)
            else:
                mods = None

            return cls(
                type=ItemStringTypeEnum.ITEM,
                id=item.id,
                bonuses=tuple(bonuses) if bonuses else None,
                mods=tuple(mods) if mods else None,
            )

    @classmethod
    def from_commodity_item(cls, item: CommodityItem) -> "ItemString":
        return cls(type=ItemStringTypeEnum.ITEM, id=item.id, bonuses=None, mods=None)

    @classmethod
    def from_protobuf(cls, proto: ItemStringPB) -> "ItemString":
        if proto.type == ItemStringTypePB.ITEM:
            type = ItemStringTypeEnum.ITEM
        elif proto.type == ItemStringTypePB.PET:
            type = ItemStringTypeEnum.PET
        else:
            raise ValueError(f"unknown type: {proto.type}")

        return cls(
            type=type,
            id=proto.id,
            bonuses=tuple(proto.bonus) if proto.bonus else None,
            mods=tuple(proto.mods) if proto.mods else None,
        )

    def to_protobuf(self) -> ItemStringPB:
        if self.type == ItemStringTypeEnum.ITEM:
            type = ItemStringTypePB.ITEM
        elif self.type == ItemStringTypeEnum.PET:
            type = ItemStringTypePB.PET
        else:
            raise ValueError(f"unknown type: {self.type}")
        return ItemStringPB(
            type=type,
            id=self.id,
            bonus=self.bonuses if self.bonuses else tuple(),
            mods=self.mods if self.mods else tuple(),
        )

    @validator("mods")
    def check_mods_even(cls, v) -> Optional[Tuple[int, ...]]:
        if v and len(v) % 2 != 0:
            raise ValueError(f"invalid mods: {v}")

        return v

    def to_str(self) -> str:
        # TODO: extensive testing
        #         """
        #         # we got pure integer id
        #         123000

        #         # this is also accepted by tsm
        #         i:123000

        #         ---
        #         # i:$id::$n_bonus:$bonus,
        #         i:193487
        #         :
        #         :2:8805:8841

        #         ---
        #         # i:$id::$n_bonus:$bonus:$n_mods:$mods
        #         # mods in [9, 29, 30]

        #         i:201942
        #         :
        #         :2:8802:8851
        #         :2:29:32:30:49

        #         ---
        #         # I guess we just ignore this case, "i" could be ilv?
        #         i:173193
        #         :
        #         :i87

        #         ----
        #         ???
        #         i:201939::+10

        #         """
        if self.bonuses:
            bonus_str = str(len(self.bonuses)) + ":" + ":".join(map(str, self.bonuses))
        else:
            bonus_str = None

        if self.mods:
            mod_str = str(len(self.mods) // 2) + ":" + ":".join(map(str, self.mods))
        else:
            mod_str = None

        if bonus_str and mod_str:
            return ":".join([self.type, str(self.id), "", bonus_str, mod_str])
        elif bonus_str:
            return ":".join([self.type, str(self.id), "", bonus_str])
        elif mod_str:
            return ":".join([self.type, str(self.id), "", "0", mod_str])
        elif self.type == "i":
            return str(self.id)
        else:
            return f"{self.type}:{self.id}"

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return f"'{str(self)}'"

    class Config:
        frozen = True


class MapItemStringMarketValueRecord(
    _BaseModelRootDictMixin[ItemString, MarketValueRecord], _BaseModel
):
    """
    data model for market value increment

    >>> map_item_string_market_value_record = {
            $item_string: $market_value_record,
            ...
        }

    """

    __root__: Dict[ItemString, MarketValueRecord] = Field(default_factory=dict)

    @classmethod
    def _heap_pop_all(cls, heap: list) -> Generator[Tuple[int, int], None, None]:
        while heap:
            yield heappop(heap)

    @classmethod
    def from_response(
        cls,
        response: GenericAuctionsResponseInterface,
        response_timestamp: int,
    ) -> "MapItemStringMarketValueRecord":

        obj = cls()
        # >>> {item_string: [total_quantity, [(price, quantity), ...]]}
        temp = {}
        min_buyout = None

        for auction in response.get_auctions():
            item_string = ItemString.from_item(auction.get_item())
            quantity = auction.get_quantity()
            price = auction.get_price()
            buyout = auction.get_buyout()
            if buyout is not None and (min_buyout is None or buyout < min_buyout):
                min_buyout = buyout

            if item_string not in temp:
                temp[item_string] = [0, []]

            temp[item_string][0] += quantity
            heappush(temp[item_string][1], (price, quantity))

        for item_string in temp:
            market_value = TSM_Math.calc_market_value(
                temp[item_string][0], cls._heap_pop_all(temp[item_string][1])
            )
            if market_value:
                obj[item_string] = MarketValueRecord(
                    timestamp=response_timestamp,
                    market_value=market_value,
                    num_auctions=temp[item_string][0],
                    min_buyout=min_buyout,
                )

        return obj


class MapItemStringMarketValueRecords(
    _BaseModelRootDictMixin[ItemString, MarketValueRecords], _BaseModel
):
    """
    >>> map_item_string_market_value_records = {
            $item_string: $market_value_records,
            ...
        }
    """

    __root__: Dict[ItemString, MarketValueRecords] = Field(
        default_factory=partial(defaultdict, MarketValueRecords)
    )

    def extend(
        self, other: "MapItemStringMarketValueRecords", sort: bool = False
    ) -> Tuple[int, int]:
        n_added_records = 0
        n_added_entries = 0
        for item_string, market_value_records in other.items():
            for market_value_record in market_value_records:
                n_added_records_, n_added_entries_ = self.add_market_value_record(
                    item_string, market_value_record, sort=False
                )
                n_added_records += n_added_records_
                n_added_entries += n_added_entries_

            if sort:
                self[item_string].sort()

        return n_added_records, n_added_entries

    def update_increment(
        self,
        increment: MapItemStringMarketValueRecord,
        sort: bool = False,
    ) -> Tuple[int, int]:
        n_added_records = 0
        n_added_entries = 0
        for item_string, record in increment.items():
            n_added_records_, n_added_entries_ = self.add_market_value_record(
                item_string, record, sort=sort
            )
            n_added_records += n_added_records_
            n_added_entries += n_added_entries_

        return n_added_records, n_added_entries

    def sort(self) -> None:
        # sort each MarketValueRecords in ascending order
        for market_value_records in self.values():
            market_value_records.sort()

    def add_market_value_record(
        self,
        item_string: ItemString,
        market_value_record: MarketValueRecord,
        sort: bool = False,
    ) -> Tuple[int, int]:
        """
        if adding records in order of ascending timestamp, set `sort=False` to
        improve performance
        """
        n_added_records = 0
        n_added_entries = 0
        if not self[item_string]:
            n_added_entries += 1
        n_added_records += self[item_string].add(market_value_record, sort=sort)
        return n_added_records, n_added_entries

    def remove_expired(self, ts_expires: int) -> Tuple[int, int]:
        n_removed_records = 0
        for market_value_records in self.values():
            n_removed_records += market_value_records.remove_expired(ts_expires)

        return n_removed_records

    def remove_empty_entries(self) -> int:
        n_removed_entries = 0
        for item_string in list(self.keys()):
            if not self[item_string]:
                self.pop(item_string)
                n_removed_entries += 1

        return n_removed_entries

    @classmethod
    def from_protobuf(cls, pb_item_db: ItemDB) -> "MapItemStringMarketValueRecords":
        o = cls()
        for pb_item in pb_item_db.items:
            market_value_records = MarketValueRecords()
            for pb_item_mv_record in pb_item.market_value_records:
                market_value_records.add(
                    MarketValueRecord(
                        timestamp=pb_item_mv_record.timestamp,
                        market_value=pb_item_mv_record.market_value,
                        num_auctions=pb_item_mv_record.num_auctions,
                        min_buyout=pb_item_mv_record.min_buyout,
                    ),
                    sort=False,
                )
            item_string = ItemString.from_protobuf(pb_item.item_string)
            o[item_string] = market_value_records

        return o

    def to_protobuf(self) -> ItemDB:
        pb_item_db = ItemDB()
        for item_string, market_value_records in self.items():
            if not market_value_records:
                # skip empty entries
                continue
            pb_item = pb_item_db.items.add()
            pb_item.item_string.CopyFrom(item_string.to_protobuf())
            for mv_record in market_value_records:
                pb_item_mv_record = pb_item.market_value_records.add()
                pb_item_mv_record.timestamp = mv_record.timestamp
                pb_item_mv_record.market_value = mv_record.market_value

        return pb_item_db

    @classmethod
    def from_protobuf_bytes(
        cls,
        data: bytes,
    ) -> "MapItemStringMarketValueRecords":
        item_db = ItemDB()
        item_db.ParseFromString(data)
        return cls.from_protobuf(item_db)

    def to_protobuf_bytes(self) -> bytes:
        return self.to_protobuf().SerializeToString()

    @classmethod
    def from_file(cls, file: BinaryFile) -> "MapItemStringMarketValueRecords":
        if not file.exists():
            raise FileNotFoundError(f"{file} not found.")

        with file.open("rb") as f:
            obj = cls.from_protobuf_bytes(f.read())
            cls._logger.info(f"{file} loaded.")
            return obj

    def to_file(self, file: BinaryFile) -> None:
        with file.open("wb") as f:
            f.write(self.to_protobuf_bytes())
            self._logger.info(f"{file} saved.")
