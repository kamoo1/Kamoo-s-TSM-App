from __future__ import annotations
import abc
import time
from typing import (
    List,
    Iterator,
    Literal,
    Union,
    Any,
    Dict,
    Optional,
    ClassVar,
    TYPE_CHECKING,
)

from pydantic import Field, root_validator

from ah.models.base import _BaseModel, StrEnum_

if TYPE_CHECKING:
    from ah.api import BNAPI


__all__ = (
    "FactionEnum",
    "RegionEnum",
    "Namespace",
    "NameSpaceCategoriesEnum",
    "GameVersionEnum",
    "TimeLeft",
    "GenericItemInterface",
    "GenericAuctionInterface",
    "GenericAuctionsResponseInterface",
    "AuctionItem",
    "Auction",
    "AuctionsResponse",
    "CommodityItem",
    "Commodity",
    "CommoditiesResponse",
)


class FactionEnum(StrEnum_):
    ALLIANCE = "a"
    HORDE = "h"

    def get_full_name(self) -> str:
        if self == self.ALLIANCE:
            return "Alliance"
        elif self == self.HORDE:
            return "Horde"
        else:
            raise ValueError(f"Invalid faction: {self}")


class RegionEnum(StrEnum_):
    US = "us"
    EU = "eu"
    KR = "kr"
    TW = "tw"


class NameSpaceCategoriesEnum(StrEnum_):
    DYNAMIC = "dynamic"
    STATIC = "static"


class GameVersionEnum(StrEnum_):
    CLASSIC = "classic1x"
    CLASSIC_WLK = "classic"
    RETAIL = ""

    # namespace, warcraft install paths, tsm slug - they all have their own
    # naming conventions...
    def get_tsm_game_version(self) -> Optional[str]:
        if self == self.CLASSIC:
            return "Classic"
        elif self == self.CLASSIC_WLK:
            return "BCC"
        elif self == self.RETAIL:
            return None
        else:
            raise ValueError(f"Invalid game version: {self!s}")

    def get_version_folder_name(self) -> str:
        if self == self.CLASSIC:
            return "_classic_era_"
        elif self == self.CLASSIC_WLK:
            return "_classic_"
        elif self == self.RETAIL:
            return "_retail_"
        else:
            raise ValueError(f"Invalid game version: {self!s}")


class Namespace(_BaseModel):
    category: NameSpaceCategoriesEnum
    game_version: GameVersionEnum
    region: RegionEnum
    SEP: ClassVar[str] = "-"

    def to_str(self) -> str:
        parts = [self.category, self.game_version, self.region]
        return self.SEP.join([p for p in parts if p])

    @classmethod
    def from_str(cls, ns: str) -> "Namespace":
        parts = ns.split(cls.SEP)
        if len(parts) == 3:
            category, game_version, region = parts
        elif len(parts) == 2:
            category, region = parts
            game_version = GameVersionEnum.RETAIL
        else:
            raise ValueError(f"Invalid namespace: {ns}")
        return cls(category=category, game_version=game_version, region=region)

    def get_locale(self) -> str:
        if self.region == RegionEnum.KR:
            return "ko_KR"
        elif self.region == RegionEnum.TW:
            return "zh_TW"
        else:
            return "en_US"

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return f'"{self}"'

    class Config(_BaseModel.Config):
        frozen = True


class TimeLeft(StrEnum_):
    VERY_LONG = "VERY_LONG"
    LONG = "LONG"
    MEDIUM = "MEDIUM"
    SHORT = "SHORT"
    VERY_SHORT = "VERY_SHORT"


class GenericItemInterface(abc.ABC):
    pass


class GenericAuctionInterface(abc.ABC):
    @abc.abstractmethod
    def get_price(
        self,
    ) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_buyout(
        self,
    ) -> Optional[int]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_quantity(
        self,
    ) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_time_left(
        self,
    ) -> TimeLeft:
        raise NotImplementedError

    @abc.abstractmethod
    def get_item(
        self,
    ) -> GenericItemInterface:
        raise NotImplementedError


class GenericAuctionsResponseInterface(abc.ABC):
    # thsese getter methods have just becomes silly with pydantic & ABC,
    # how can I properly declare these as abstract properties while with pydantic?
    @abc.abstractmethod
    def get_auctions(
        self,
    ) -> Iterator[GenericAuctionInterface]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_timestamp(
        self,
    ) -> Iterator[GenericAuctionInterface]:
        raise NotImplementedError

    @abc.abstractclassmethod
    def from_api(
        self,
        api: BNAPI,
    ) -> "GenericAuctionsResponseInterface":
        raise NotImplementedError


class AuctionItem(GenericItemInterface, _BaseModel):
    """
    >>> item = {
        'id': 199032,
        'context': 27,
        'bonus_lists': [
            7969,
            6652,
            1678
        ],
        'modifiers': [
            {'type': 9, 'value': 70},
            {'type': 28, 'value': 2437}
        ],
        # pet attributes, all present or none present
        "pet_breed_id": 5,
        "pet_level": 25,
        "pet_quality_id": 3,
        "pet_species_id": 1523
    }
    """

    id: int
    context: Optional[int] = None
    bonus_lists: Optional[List[int]] = None
    modifiers: Optional[
        List[Dict[Union[Literal["type"], Literal["value"]], int]]
    ] = None
    pet_breed_id: Optional[int] = None
    pet_level: Optional[int] = None
    pet_quality_id: Optional[int] = None
    pet_species_id: Optional[int] = None

    # NOTE: these fields are part of classic & classic wlk, but not retail
    seed: Optional[int] = None
    rand: Optional[int] = None

    @root_validator(pre=True)
    def check_pet_fields(cls, values):
        pet_fields = ["pet_breed_id", "pet_level", "pet_quality_id", "pet_species_id"]
        if any(values.get(f) for f in pet_fields):
            if not all(values.get(f) for f in pet_fields):
                raise ValueError("Missing pet field")

        return values


class Auction(GenericAuctionInterface, _BaseModel):
    """

    >>>  auction = {
            # auction id
            "id": 123,
            "item": $auction_item,
            # at least one of `bid` `buyout`
            "bid": 10000,
            "buyout": 28000000,
            "quantity": 1,
            "time_left": "SHORT"
        }
    """

    # TODO: test bid only auctions
    id: int
    item: AuctionItem
    # one of bid and buyout needs be present
    bid: Optional[int] = None
    buyout: Optional[int] = None
    quantity: int
    time_left: TimeLeft

    @root_validator(pre=True)
    def check_bid_buyout(cls, values):
        if values.get("bid") is None and values.get("buyout") is None:
            raise ValueError("At least one of 'bid' and 'buyout' needs to be present")

        return values

    def get_price(self) -> int:
        return self.buyout or self.bid

    def get_buyout(self) -> Optional[int]:
        return self.buyout

    def get_quantity(self) -> int:
        return self.quantity

    def get_time_left(self) -> TimeLeft:
        return self.time_left

    def get_item(self) -> GenericItemInterface:
        return self.item


class AuctionsResponse(GenericAuctionsResponseInterface, _BaseModel):
    """

    >>> auctions_response = {
            "_links": {
                "self": {
                    "href": "..."
                }
            },
            "connected_realm": {
                "href": "..."
            },
            "auctions": [
                $auction,
                ...
            ],
            "commodities": {
                "href": "..."
            }
        }
    """

    auctions: List[Auction]
    timestamp: int = Field(default_factory=lambda: int(time.time()))

    # don't care, `Any` implies optional field
    commodities: Any
    links: Any = Field(alias="_links")
    connected_realm: Any

    # NOTE: these fields are part of classic & classic wlk, but not retail
    id: Any
    name: Any

    def get_auctions(self) -> List[GenericAuctionInterface]:
        return self.auctions

    def get_timestamp(self) -> int:
        return self.timestamp

    @classmethod
    def from_api(
        cls,
        bn_api: BNAPI,
        namespace: Namespace,
        connected_realm_id: str,
        faction: FactionEnum,
    ) -> "AuctionsResponse":
        resp = bn_api.pull_auctions(namespace, connected_realm_id, faction=faction)
        return cls.parse_obj(resp)


class CommodityItem(GenericItemInterface, _BaseModel):
    """
    >>> commodity_item = {
            "id": 3857
        }
    """

    id: int


class Commodity(GenericAuctionInterface, _BaseModel):
    """

    >>> commodity = {
            # auction id
            "id": 123,
            "item": $commodity_item,
            "quantity": 1,
            "unit_price": 100,
            "time_left": "VERY_LONG",
        }
    """

    id: int
    item: CommodityItem
    quantity: int
    unit_price: int
    time_left: TimeLeft

    def get_price(self) -> int:
        return self.unit_price

    def get_buyout(self) -> Optional[int]:
        return self.unit_price

    def get_quantity(self) -> int:
        return self.quantity

    def get_time_left(self) -> TimeLeft:
        return self.time_left

    def get_item(self) -> GenericItemInterface:
        return self.item


class CommoditiesResponse(GenericAuctionsResponseInterface, _BaseModel):
    """

    >>> commodities_response = {
            "_links": {
                "self": {
                    "href": "..."
                }
            },
            "auctions": [
                $commodity,
                ...
            ],
        }
    """

    # we don't care about _links
    links: Any = Field(alias="_links")
    auctions: List[Commodity]
    timestamp: int = Field(default_factory=lambda: int(time.time()))

    def get_auctions(self) -> List[GenericAuctionInterface]:
        return self.auctions

    @classmethod
    def from_api(cls, bn_api: BNAPI, namespace: Namespace) -> "CommoditiesResponse":
        resp = bn_api.pull_commodities(namespace)
        return cls.parse_obj(resp)

    def get_timestamp(self) -> int:
        return self.timestamp
