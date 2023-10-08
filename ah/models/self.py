from __future__ import annotations
from functools import partial
from heapq import heappush, heappop
from collections import defaultdict
from logging import Logger, getLogger
from copy import deepcopy
from functools import total_ordering, lru_cache, reduce
from itertools import chain
import json
from typing import (
    List,
    Dict,
    ClassVar,
    Generator,
    Tuple,
    Optional,
    Union,
    Iterable,
    Set,
    TYPE_CHECKING,
)

import numpy as np
from attrs import define, field, Factory

from ah.protobuf.item_db_pb2 import (
    ItemDB,
    ItemString as ItemStringPB,
    ItemStringType as ItemStringTypePB,
)
from ah.storage import BinaryFile, TextFile
from ah.models.base import (
    _RootDictMixin,
    _RootListMixin,
    ConverterWrapper as CW,
    StrEnum_,
    IntEnum_,
)
from ah.models.blizzard import (
    Namespace,
    GenericAuctionsResponseInterface,
    GenericItemInterface,
    AuctionItem,
    CommodityItem,
    FactionEnum,
    GameVersionEnum,
    ConnectedRealm,
)
from ah.defs import SECONDS_IN
from ah.data import map_bonuses

if TYPE_CHECKING:
    from ah.db import GithubFileForker

__all__ = (
    "DBTypeEnum",
    "DBExtEnum",
    "DBFileName",
    "MarketValueRecord",
    "MarketValueRecords",
    "ItemStringTypeEnum",
    "ItemString",
    "MapItemStringMarketValueRecords",
    "MapItemStringMarketValueRecord",
    "Meta",
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


class DBTypeEnum(StrEnum_):
    AUCTIONS = "auctions"
    COMMODITIES = "commodities"
    META = "meta"


class DBExtEnum(StrEnum_):
    GZ = "gz"
    BIN = "bin"
    JSON = "json"


@define(kw_only=True, frozen=True)
class DBFileName:
    _logger: ClassVar[Logger] = getLogger("DBFileName")
    namespace: Namespace = field(converter=CW.norm(Namespace.from_str, Namespace))
    db_type: DBTypeEnum = field(converter=CW.norm(DBTypeEnum))
    crid: Optional[int] = field(default=None, converter=CW.optional(int))
    faction: Optional[FactionEnum] = field(
        default=None, converter=CW.optional(CW.norm(FactionEnum))
    )
    ext: DBExtEnum = field(converter=CW.norm(DBExtEnum))
    SEP: ClassVar[str] = "_"
    SEP_EXT: ClassVar[str] = "."

    def __attrs_post_init__(self) -> None:
        self.validate_root()

    def validate_root(self):
        # if db_type == META, then ext must be JSON
        # elif db_type in (AUCTIONS, COMMODITIES), then ext must in (BIN, GZ)
        # else: raise ValueError
        if self.db_type == DBTypeEnum.META:
            if self.ext != DBExtEnum.JSON:
                raise ValueError("ext must be JSON if db_type.type is META")
        elif self.db_type in (DBTypeEnum.COMMODITIES, DBTypeEnum.AUCTIONS):
            if self.ext not in (DBExtEnum.BIN, DBExtEnum.GZ):
                raise ValueError(
                    "ext must be BIN or GZ if db_type.type is COMMODITIES or AUCTIONS"
                )
        else:
            raise ValueError(f"Invalid db_type: {self.db_type}")

        # if db_type == AUCTIONS, then crid must be set
        # elif db_type in (META, COMMODITIES), then crid must be None
        # else: raise ValueError
        if self.db_type == DBTypeEnum.AUCTIONS:
            if self.crid is None:
                raise ValueError("crid must be set if db_type.type is AUCTIONS")
        elif self.db_type in (DBTypeEnum.META, DBTypeEnum.COMMODITIES):
            if self.crid is not None:
                raise ValueError(
                    "crid must be None if db_type.type is META or COMMODITIES"
                )
        else:
            raise ValueError(f"Invalid db_type: {self.db_type}")

        # if db_type == COMMODITIES, then namespace.game_version must be RETAIL
        if self.db_type == DBTypeEnum.COMMODITIES:
            if self.namespace.game_version != GameVersionEnum.RETAIL:
                raise ValueError(
                    "db_type.type cannot be COMMODITIES if namespace is not RETAIL"
                )

        # if namespace.game_version == RETAIL then faction must be None
        # elif namespace.game_version in (CLASSIC, CLASSIC_WLK)
        #     if db_type != META, then faction must be set
        # else: raise ValueError
        if self.namespace.game_version == GameVersionEnum.RETAIL:
            if self.faction is not None:
                raise ValueError(
                    "faction must be None if namespace.game_version is RETAIL"
                )
        elif self.namespace.game_version in (
            GameVersionEnum.CLASSIC,
            GameVersionEnum.CLASSIC_WLK,
        ):
            if self.db_type != DBTypeEnum.META and self.faction is None:
                raise ValueError(
                    "faction must be set if namespace.game_version is "
                    "CLASSIC or CLASSIC_WLK and db_type.type is not META"
                )

    def is_compress(self) -> bool:
        return self.ext == DBExtEnum.GZ

    def to_str(self) -> str:
        parts = filter(
            lambda x: x is not None,
            [self.namespace, self.db_type, self.crid, self.faction],
        )
        parts = map(lambda s: s if isinstance(s, str) else str(s), parts)
        return f"{self.SEP.join(parts)}{self.SEP_EXT}{self.ext}"

    @classmethod
    def from_str(cls, name: str) -> "DBFileName":
        name, ext = name.split(cls.SEP_EXT)
        parts = name.split(cls.SEP)
        # possible parts:
        # 1. namespace, db_type, crid, faction
        # 2. namespace, db_type, crid
        # 3. namespace, db_type

        # pad parts with None
        parts += [None] * (4 - len(parts))
        namespace, db_type, crid, faction = parts
        return cls(
            namespace=namespace,
            db_type=db_type,
            crid=crid,
            faction=faction,
            ext=ext,
        )

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        # wrapping quotes to repr sometimes confuses me misinterpreting
        # it's a string.
        return f'"{self}"'


@define(kw_only=True)
@total_ordering
class MarketValueRecord:
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

    _logger: ClassVar[Logger] = getLogger("MarketValueRecord")
    timestamp: np.int32 = field(converter=np.int32)
    market_value: Optional[np.int64] = field(converter=CW.optional(np.int64))
    num_auctions: np.int32 = field(converter=np.int32)
    min_buyout: Optional[np.int64] = field(
        default=None, converter=CW.optional(np.int64)
    )

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp


@define(kw_only=True)
class MarketValueRecords(_RootListMixin[MarketValueRecord]):
    """
    Holds an list of MarketValueRecord, ordered by timestamp in ascending order.

    >>> market_value_records = [
            $market_value_record,
            ...
        ]
    """

    _logger: ClassVar[Logger] = getLogger("MarketValueRecords")
    __root__: List[MarketValueRecord] = field(default=Factory(list), alias="__root__")
    DAY_WEIGHTS: ClassVar[List[int]] = [
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

    def compress(self, ts_now: int, ts_expires_in: int) -> int:
        """average all records in the range of 1 day down to 1 record,
        the average sample range is `[mid_day - 12hr, mid_day + 12hr]`
        the averaged record's timestamp is the mid_day.
        """
        # keep recent records that didn't span over a day
        ts_end = ts_now - ts_now % SECONDS_IN.DAY
        # round up so we don't miss any records
        n_days = (ts_expires_in + SECONDS_IN.DAY - 1) // SECONDS_IN.DAY
        comporessed_records = self.average_by_day(
            self,
            ts_end,
            n_days,
            return_compressed_record=True,
        )
        comporessed_records = (
            record for record in comporessed_records if record is not None
        )
        n_before = len(self)
        # remove records that gets compressed
        self.remove_expired(ts_end)
        # prepend compressed records
        self.__root__ = [*comporessed_records, *self]
        n_after = len(self)
        return n_before - n_after

    def remove_expired(self, ts_expires: int) -> int:
        """remove records that are older than `ts_expires` (timestamp < ts_expires)"""
        len_before = len(self)
        self.__root__ = [record for record in self if record.timestamp >= ts_expires]
        return len_before - len(self)

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
        return_compressed_record: bool = False,
    ) -> List[Union[MarketValueRecord, float, None]]:
        """
        average range is (ts_now - n_days_before * SECONDS_IN.DAY, ts_now),
        range end (ts_now) is exclusive following convention,
        records with timestamp >= ts_now are ignored.

        note that records should be passed in ascending order
        """
        # 1. put market value snapshots into buckets of 1 day
        buckets = defaultdict(list)
        for record in reversed(records):
            if record.market_value is None:
                continue
            # every `n * SECONDS_IN.DAY` is the start of a new day
            i = (ts_now - record.timestamp - 1) // SECONDS_IN.DAY
            if i < 0:
                continue

            elif i < n_days_before:
                buckets[i].append(record)

            elif is_records_sorted:
                # if records are sorted in descending order, we can stop
                # processing them when we reach the first record that is
                # older than `n_days_before`
                break

        # 2. average each bucket so we get averaged market value for each day
        #    note that some buckets may be empty, indicated by `None` instead
        #    of an average.
        days_average = [None] * n_days_before
        for i, records in buckets.items():
            if not records:
                continue

            day = n_days_before - i - 1
            n_records = len(records)
            avg_market_value = sum(r.market_value for r in records) / n_records
            avg_market_value = int(avg_market_value + 0.5)

            if return_compressed_record:
                avg_num_auctions = sum(r.num_auctions for r in records) / n_records
                avg_num_auctions = int(avg_num_auctions + 0.5)
                min_min_buyout = min(record.min_buyout for record in records)
                # mid-day timestamp
                time_stamp = int(ts_now - (i + 0.5) * SECONDS_IN.DAY)
                days_average[day] = MarketValueRecord(
                    timestamp=time_stamp,
                    market_value=avg_market_value,
                    num_auctions=avg_num_auctions,
                    min_buyout=min_min_buyout,
                )
            else:
                days_average[day] = avg_market_value

        return days_average

    def get_historical_market_value(self, ts_now: int) -> int:
        # TSM says it's a 60-day average of "weighted market value", I'm just
        # getting lazy here using average of records instead.

        # To take uneven updates per day into account, we'd first get the average
        # market values for each day, for a total of 60 days, and then calculate
        # the average of those 60 days.

        if not self:
            self._logger.debug(
                f"{self}: no records, get_historical_market_value() returns 0"
            )
            return 0
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
            self._logger.debug(
                f"{self}: all records expired, get_historical_market_value() returns 0"
            )
            return 0

        return int(sum_market_value / n_days + 0.5)

    def get_weighted_market_value(self, ts_now: int) -> int:
        if not self:
            self._logger.debug(
                f"{self}: no records, get_weighted_market_value() returns 0"
            )
            return 0

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
            # XXX: This occurs fairly often, if no records found in recent 15 days
            # self._logger.debug(
            #     f"{self}: all records expired, get_weighted_market_value() returns 0"
            # )
            return 0


class ItemStringTypeEnum(StrEnum_):
    PET = "p"
    ITEM = "i"


class ILVL_MODIFIERS_TYPES(IntEnum_):
    ABS_ILVL = -1
    REL_ILVL = -2


@define(kw_only=True, frozen=True, cache_hash=True)
class ItemString:
    """This is a frozen model, it has a __hash__ method generated by attrib
    that calcueates the hash value from the model's immutable fields.

    To instantiating this model in anyway other than `from_item` (not recommended):
    - Sort the `mods` fields, `mods` is an tuple (i, i+1, ...)
      transformed from a dict where `i` is the key and `i+1` is `i`'s value.
      the dict is sorted by key in ascending order.

    - Filter the `mods` field, only keep the key-value pairs where the key is
      in `KEEPED_MODIFIERS_TYPES`.

    - Filter the `bonuses` field by the keys of `MAP_BONUSES`, in case of the
      corresponding dict value of `MAP_BONUSES` contains any field in listed in
      `SET_BONUS_ILVL_FIELDS`, filter out that bonus id as well. (???)

    - Sort the `bonuses` field, `bonuses` is a tuple of ints.

    - Pets don't have `mods` or `bonuses` fields, they take `breed_id` from
      `AuctionItem` as their `id` field.

    item strings from DB will get instantiated by `from_protobuf`, which doesn't
    go through the pre-processing steps as in `from_item`. in case of `MAP_BONUSES`
    getting updated by Blizzard causing the hash of `ItemString` to change within
    the same item: only newly added records will be affected, old records of such
    items will eventually expire and get removed from DB.
    """

    _logger: ClassVar[Logger] = getLogger("ItemString")
    type: ItemStringTypeEnum = field(converter=CW.norm(ItemStringTypeEnum))
    id: np.int32 = field(converter=np.int32)
    bonuses: Optional[Tuple[np.int32, ...]] = field(
        converter=CW.optional(CW.iter(tuple, np.int32))
    )
    # [1.2, 2.3, 3] | None -> opentional
    # [1.2, 2.3, 3]        -> tuple(np.int32)
    # (1, 2, 3)
    # used to be kv pairs, cast to even-length tuple for easy hashing
    mods: Optional[Tuple[np.int32, ...]] = field(
        converter=CW.optional(CW.iter(tuple, np.int32))
    )

    KEEPED_MODIFIERS_TYPES: ClassVar[List[int]] = [9, 29, 30]
    MAP_BONUSES: ClassVar[Dict] = map_bonuses
    SET_BONUS_ILVL_FIELDS: ClassVar[Set[str]] = {
        "level",
        "base_level",
        "curveId",
        "points",
    }
    MOD_TYPE_PLAYER_LEVEL: ClassVar[int] = 9
    DEFAULT_PLAYER_LVL: ClassVar[int] = 1

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
        if item.pet_species_id is not None:
            return cls(
                type=ItemStringTypeEnum.PET,
                id=item.pet_species_id,
                bonuses=None,
                mods=None,
            )

        else:
            if item.bonus_lists:
                # we will not sort bonus ids as for now
                bonuses = list(filter(cls.MAP_BONUSES.__contains__, item.bonus_lists))

            else:
                bonuses = None

            plvl = None
            heap = []
            if item.modifiers:
                for mod in item.modifiers:
                    mod_type = mod["type"]
                    mod_value = mod["value"]
                    if mod_type not in cls.KEEPED_MODIFIERS_TYPES:
                        continue
                    if mod_type == cls.MOD_TYPE_PLAYER_LEVEL:
                        plvl = mod_value
                    heappush(heap, (mod_type, mod_value))
                mods = []
                while heap:
                    mod_type, mod_value = heappop(heap)
                    mods.append(mod_type)
                    mods.append(mod_value)
            else:
                mods = None

            ilvl_info = None
            try:
                ilvl_info = cls.get_ilvl(bonuses, plvl)
            except Exception:
                cls._logger.exception("Exception raised when calculating ilvl:")

            # TODO: figure out if sort bonuses or not
            bonuses = sorted(bonuses) if bonuses else None

            if ilvl_info is None:
                return cls(
                    type=ItemStringTypeEnum.ITEM,
                    id=item.id,
                    bonuses=tuple(bonuses) if bonuses else None,
                    mods=tuple(mods) if mods else None,
                )
            else:
                # ilvl itemstring don't have bonuses or mods in their .to_str(),
                # so all leftover bonuses and mods will be discarded.
                # in order to actually store ilvl, we made up two negative mod keys
                # as storage but they will never show up in the .to_str() as regular
                # mods.
                ilvl, is_relative = ilvl_info
                if is_relative:
                    o = cls(
                        type=ItemStringTypeEnum.ITEM,
                        id=item.id,
                        bonuses=None,
                        mods=(ILVL_MODIFIERS_TYPES.REL_ILVL, ilvl),
                    )

                else:
                    o = cls(
                        type=ItemStringTypeEnum.ITEM,
                        id=item.id,
                        bonuses=None,
                        mods=(ILVL_MODIFIERS_TYPES.ABS_ILVL, ilvl),
                    )

                return o

    @classmethod
    def get_ilvl(
        cls, bonuses: List[int], plvl: Optional[int]
    ) -> Optional[Tuple[int, bool]]:
        if not bonuses:
            return None

        if plvl is None:
            plvl = cls.DEFAULT_PLAYER_LVL
        ilvl_rel = None
        ilvl_base = None
        # last_curve_info = None
        last_curve_bid = None
        for bid in bonuses:
            binfo = cls.MAP_BONUSES[bid]
            if "level" in binfo:
                delta = binfo["level"]
                ilvl_rel = delta if ilvl_rel is None else ilvl_rel + delta

            elif "base_level" in binfo:
                ilvl_base = ilvl_base or binfo["base_level"]

            elif "curveId" in binfo:
                # there might be multiple curves and we need to
                # sort them, TSM's sorting rule is:
                # flat1, flat2 -> max(bonus1, bonus2)
                # curve1, any2 -> max(curve1.bonus, curve2.bonus or inf)
                # flat, curve-> no sorting
                #
                # To clarify:
                # curve, curve -> keep the one with higher curve id
                # curve, flat or flat, curve -> keep flat
                # flat, flat -> keep the one with higher bonus id
                #
                # I think we can sort all tyeps of curves by curve id,
                # TSM ditched the curve id field for flat curves,
                # therefore it fallback to bonus id instead?

                # TODO: read wowhead tooltip code
                if last_curve_bid:
                    # sort by curve id
                    last_curve_bid = (
                        last_curve_bid
                        if cls.MAP_BONUSES[last_curve_bid]["curveId"]
                        > cls.MAP_BONUSES[bid]["curveId"]
                        else bid
                    )

                else:
                    last_curve_bid = bid

        if not (ilvl_base or ilvl_rel or last_curve_bid):
            # no ilvl info
            return None

        elif last_curve_bid is None:
            if ilvl_base is None:
                return ilvl_rel, True
            else:
                ilvl = ilvl_base if ilvl_rel is None else ilvl_base + ilvl_rel
                if ilvl < 0:
                    return None
                else:
                    return ilvl, False

        else:
            # according to TSM's we can simply ignore the base ilvl
            # and the relative ilvl if there is a curve
            ilvl = cls.get_ilvl_from_curve(last_curve_bid, plvl)
            if ilvl is None or ilvl < 0:
                return None
            else:
                return ilvl, False

    @classmethod
    @lru_cache(1024 * 512)
    # def get_ilvl_from_curve(cls, curve_points: List[Dict], plvl=DEFAULT_PLAYER_LVL):
    def get_ilvl_from_curve(cls, bonus_id: int, plvl: int) -> Optional[int]:
        curve_points = cls.MAP_BONUSES[bonus_id]["points"]
        # >>> curve_points = [
        #     # [player_level, item_level]; sorted by player_level
        #     [1, 10],
        #     [2, 20],
        #     ...
        # ]
        if not curve_points:
            raise ValueError("Invalid curve points")

        # assuming it's soreted by player level
        plvl = max(plvl, curve_points[0][0])
        plvl = min(plvl, curve_points[-1][0])
        point1, point2 = None, None
        for point in curve_points:
            if point[0] == plvl:
                return point[1]
            elif point[0] > plvl:
                point2 = point
                break
            else:
                point1 = point

        if not point1 or not point2:
            # I don't think this could ever happen...
            raise ValueError("Invalid curve points")

        # linear interpolation
        plvl1, ilvl1 = point1[0], point1[1]
        plvl2, ilvl2 = point2[0], point2[1]
        return int((plvl - plvl1) * (ilvl2 - ilvl1) / (plvl2 - plvl1) + ilvl1 + 0.5)

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

    @mods.validator
    def check_mods_even(cls, k, v) -> Optional[Tuple[int, ...]]:
        if v and len(v) % 2 != 0:
            raise ValueError(f"invalid mods: {v}")

        return v

    def to_str(self) -> str:
        # TODO: extensive testing
        if self.mods and self.mods[0] in (e.value for e in ILVL_MODIFIERS_TYPES):
            ilvl_key = self.mods[0]
            ilvl_val = self.mods[1]
            if ilvl_key == ILVL_MODIFIERS_TYPES.ABS_ILVL:
                return f"{self.type}:{self.id}::i{ilvl_val}"
            else:
                return f"{self.type}:{self.id}::{'+' if ilvl_val > 0 else ''}{ilvl_val}"

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


@define(kw_only=True)
class MapItemStringMarketValueRecord(_RootDictMixin[ItemString, MarketValueRecord]):
    """
    data model for market value increment

    >>> map_item_string_market_value_record = {
            $item_string: $market_value_record,
            ...
        }

    """

    _logger: ClassVar[Logger] = getLogger("MapItemStringMarketValueRecord")
    __root__: Dict[ItemString, MarketValueRecord] = field(
        default=Factory(dict), alias="__root__"
    )
    MAX_JUMP_MUL: ClassVar[float] = 1.2
    MAX_STD_MUL: ClassVar[float] = 1.5
    SAMPLE_LO: ClassVar[float] = 0.15
    SAMPLE_HI: ClassVar[float] = 0.3

    @classmethod
    def calc_market_value(cls, item_n: int, price_groups: Iterable[Tuple[int, int]]):
        """calculate market value from a list of (price, quantity) tuples
        `price_groups` is a list of tuples of (price, quantity), sorted by price.
        a older version of this function used to take just a list of prices (by
        inflating `price_groups`) - albeit the intuitiveness, takes 10x more time to
        run.

        sources:
        https://web.archive.org/web/20200609203103/https://support.tradeskillmaster.com/display/KB/AuctionDB+Market+Value
        https://github.com/WouterBink/TradeSkillMaster-1/blob/master/TradeSkillMaster_AuctionDB/Modules/data.lua
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

    @classmethod
    def _heap_pop_all(cls, heap: list) -> Generator[Tuple[int, int], None, None]:
        while heap:
            yield heappop(heap)

    @classmethod
    def from_response(
        cls,
        response: GenericAuctionsResponseInterface,
        game_version: GameVersionEnum = GameVersionEnum.RETAIL,
    ) -> "MapItemStringMarketValueRecord":
        obj = cls()
        # >>> {item_string: [total_quantity, [(price, quantity), ...]]}
        temp = {}

        for auction in response.get_auctions():
            item_string = ItemString.from_item(auction.get_item())
            quantity = auction.get_quantity()
            # for auction, price = .buyout or .bid; buyout = .buyout
            # for commodity, price = .buyout; buyout = .buyout
            price = auction.get_price()
            buyout = auction.get_buyout()
            if game_version in (GameVersionEnum.CLASSIC, GameVersionEnum.CLASSIC_WLK):
                # for classic, prices are per stack
                buyout = None if buyout is None else buyout // quantity
                price = None if price is None else price // quantity

            if item_string not in temp:
                # >>> [total_quantity, min_buyout, [(price, quantity), ...]]
                temp[item_string] = [0, None, []]

            temp[item_string][0] += quantity
            if buyout is not None and (
                temp[item_string][1] is None or buyout < temp[item_string][1]
            ):
                temp[item_string][1] = buyout

            # we're using bid as price for auctions without buyout
            heappush(temp[item_string][2], (price, quantity))

        for item_string in temp:
            market_value = cls.calc_market_value(
                temp[item_string][0], cls._heap_pop_all(temp[item_string][2])
            )
            if market_value:
                obj[item_string] = MarketValueRecord(
                    timestamp=response.get_timestamp(),
                    market_value=market_value,
                    num_auctions=temp[item_string][0],
                    # for auctions without buyout, their min_buyout are set 0
                    min_buyout=temp[item_string][1] or 0,
                )

        return obj


@define(kw_only=True)
class MapItemStringMarketValueRecords(_RootDictMixin[ItemString, MarketValueRecords]):
    """
    >>> map_item_string_market_value_records = {
            $item_string: $market_value_records,
            ...
        }
    """

    _logger: ClassVar[Logger] = getLogger("MapItemStringMarketValueRecords")
    __root__: Dict[ItemString, MarketValueRecords] = field(
        default=Factory(partial(defaultdict, MarketValueRecords)),
        alias="__root__",
    )
    _item_id_map: Dict[int, ItemString] = field(
        init=False,
        default=Factory(partial(defaultdict, list)),
        repr=False,
    )
    _pet_id_map: Dict[int, ItemString] = field(
        init=False,
        default=Factory(partial(defaultdict, list)),
        repr=False,
    )
    _indexed: bool = field(
        init=False,
        default=False,
        repr=False,
    )

    def _init_id_maps(self) -> None:
        """build indexes on top of item_string for the need of querying
        by numeric id
        """
        if self._indexed:
            return
        for item_string in self.keys():
            if item_string.type == ItemStringTypeEnum.ITEM:
                self._item_id_map[item_string.id].append(item_string)
            elif item_string.type == ItemStringTypeEnum.PET:
                self._pet_id_map[item_string.id].append(item_string)

        self._indexed = True

    # todo add from_str to item_string so we can indexing easily here
    def query(self, id_: int) -> "MapItemStringMarketValueRecords":
        self._init_id_maps()
        result = MapItemStringMarketValueRecords()
        if id_ in self._item_id_map and self._item_id_map[id_]:
            for item_string in self._item_id_map[id_]:
                result[item_string] = deepcopy(self[item_string])

        if id_ in self._pet_id_map and self._pet_id_map[id_]:
            for item_string in self._pet_id_map[id_]:
                result[item_string] = deepcopy(self[item_string])

        return result

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

    def compress(
        self,
        ts_now: int,
        ts_expires_in: int,
    ) -> int:
        n_removed = 0
        for market_value_records in self.values():
            n_removed += market_value_records.compress(ts_now, ts_expires_in)

        return n_removed

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
                pb_item_mv_record.num_auctions = mv_record.num_auctions
                pb_item_mv_record.min_buyout = mv_record.min_buyout

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
    def from_file(
        cls, file: BinaryFile, forker: GithubFileForker = None
    ) -> "MapItemStringMarketValueRecords":
        if forker:
            forker.ensure_file(file)

        if not file.exists():
            cls._logger.info(
                f"{file!r} not found, returning empty {cls.__name__!r} object."
            )
            return cls()

        with file.open("rb") as f:
            obj = cls.from_protobuf_bytes(f.read())
            cls._logger.info(f"{file} loaded.")
            return obj

    def to_file(self, file: BinaryFile) -> None:
        with file.open("wb") as f:
            f.write(self.to_protobuf_bytes())
            self._logger.info(f"{file} saved.")


class Meta:
    _logger = getLogger("Meta")

    def __init__(self, data: Dict = None) -> None:
        """
        we store meta data in a json file, the structure is as follows:
        >>> {
                "update": {
                    "start_ts": 0,
                    "end_ts": 0,
                    "duration": 0,
                },
                "connected_realms": {
                    $connected_realm_id: [
                        {
                            "name": $realm_name(native),
                            "id": $realm_id,
                            "slug": $realm_slug,
                            "is_hardcore": $is_hardcore(bool),
                        },
                        ...
                    ],
                    ...
                },
                "system": {...}
            }

        """

        self._data = data or {
            "update": {
                "start_ts": None,
                "end_ts": None,
                "duration": None,
            },
            "connected_realms": {},
        }

    def add_connected_realm(self, crid: int, connected_realm: ConnectedRealm) -> None:
        realms = []
        for realm in connected_realm.realms:
            realms.append(
                {
                    "name": realm.name,
                    "id": realm.id,
                    "slug": realm.slug,
                    "is_hardcore": realm.is_hardcore(),
                }
            )

        if crid != connected_realm.id:
            self._logger.critical(
                f"connected realm id mismatch: req {crid=}, resp {connected_realm.id=}"
            )
            raise ValueError("connected realm id mismatch")

        self._data["connected_realms"][connected_realm.id] = realms

    def set_update_ts(self, start_ts: int, end_ts: int) -> None:
        self._data["update"]["start_ts"] = start_ts
        self._data["update"]["end_ts"] = end_ts
        self._data["update"]["duration"] = end_ts - start_ts

    def set_system(self, system: Dict) -> None:
        self._data["system"] = system

    def get_connected_realm_ids(self) -> Tuple[int]:
        return tuple(map(int, self._data["connected_realms"].keys()))

    def get_connected_realm_names(self) -> Tuple[str]:
        return tuple(
            map(
                lambda x: x["name"],
                chain.from_iterable(self._data["connected_realms"].values()),
            )
        )

    def iter_connected_realms(
        self,
    ) -> Generator[Tuple[int, Set[str], bool], None, None]:
        for crid, crs in self._data["connected_realms"].items():
            if not crs:
                continue
            # make sure realms are same type (hardcore or not)
            n_hc = reduce(lambda s, realm: s + 1 if realm["is_hardcore"] else s, crs, 0)
            if not (n_hc == 0 or n_hc == len(crs)):
                self._logger.warning(
                    f"connected realm {crid=} contains realms of different types!"
                )

            cr_names = set()
            for realm in crs:
                cr_names.add(realm["name"])

            is_hc = n_hc == len(crs)
            yield crid, cr_names, is_hc

    def get_update_ts(self) -> Tuple[int, int]:
        return self._data["update"]["start_ts"], self._data["update"]["end_ts"]

    @classmethod
    def from_file(cls, file: TextFile, forker: GithubFileForker = None) -> "Meta":
        if forker:
            forker.ensure_file(file)

        if not file.exists():
            cls._logger.info(
                f"{file!r} not found, returning empty {cls.__name__!r} object."
            )
            return cls()

        with file.open("r") as f:
            data = json.load(f)

        # convert keys to int
        data["connected_realms"] = {
            int(k): v for k, v in data["connected_realms"].items()
        }
        meta = cls(data=data)
        cls._logger.info(f"{file} loaded.")
        return meta

    def to_file(self, file: TextFile) -> None:
        # convert keys to str
        data = deepcopy(self._data)
        data["connected_realms"] = {
            str(k): v for k, v in self._data["connected_realms"].items()
        }
        with file.open("w") as f:
            json.dump(data, f, indent=4)
        self._logger.info(f"{file} saved.")
