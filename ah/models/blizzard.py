import abc
import time
from enum import Enum
from typing import List, Iterator, Literal, Union, Any, Dict, Optional

from pydantic import Field, root_validator
from pydantic.main import ModelMetaclass

from ah.models.base import _BaseModel
from ah.api import API

__all__ = (
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


class TimeLeft(str, Enum):
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
        api: API,
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

    # don't care, `Any` implies optional field
    links: Any = Field(alias="_links")
    # don't care
    connected_realm: Any
    auctions: List[Auction]
    # don't care
    commodities: Any
    timestamp: int = Field(default_factory=lambda: int(time.time()))

    def get_auctions(self) -> List[GenericAuctionInterface]:
        return self.auctions

    def get_timestamp(self) -> int:
        return self.timestamp

    @classmethod
    def from_api(
        cls, api: API, region: str, connected_realm_id: str
    ) -> "AuctionsResponse":
        resp = api.get_auctions(region, connected_realm_id)
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
    def from_api(cls, api: API, region: str) -> "CommoditiesResponse":
        resp = api.get_commodities(region)
        return cls.parse_obj(resp)

    def get_timestamp(self) -> int:
        return self.timestamp
