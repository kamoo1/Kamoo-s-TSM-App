import sys
from typing import ClassVar, Generic, Iterator, TypeVar, Callable, Type, Any
from logging import getLogger, Logger

from pydantic import ConfigDict, BaseModel

__all__ = (
    "_BaseModel",
    "_RootListMixin",
    "_RootDictMixin",
    "ConverterWrapper",
    "StrEnum_",
    "IntEnum_",
)

_VT = TypeVar("_VT")
_KT = TypeVar("_KT")

_ITEMS_T = TypeVar("_ITEMS_T")
_ITEM_T = TypeVar("_ITEM_T")


# if python 3.11+, use `enum.StrEnum` instead of `str, enum.Enum`
# https://github.com/python/cpython/issues/100458
if sys.version_info >= (3, 11):
    from enum import StrEnum as StrEnum_, IntEnum as IntEnum_

else:
    from enum import Enum

    # Note: must not use `type`
    # https://stackoverflow.com/questions/69328274
    class StrEnum_(str, Enum):
        # Add `__str__` to make it behave as expected in case of `str(enum)`
        # https://blog.pecar.me/python-enum
        def __str__(self) -> str:
            return self.value

    class IntEnum_(int, Enum):
        pass


class ConverterWrapper:
    @staticmethod
    def optional(converter: Callable) -> Callable:
        """Make a converter ignores None values."""

        def wrapped(value: str) -> str:
            if value is None:
                return None

            return converter(value)

        return wrapped

    @staticmethod
    def iter(
        items_converter: Callable[[Iterator], Type[_ITEMS_T]],
        item_converter: Callable[[Any], _ITEM_T],
    ) -> Callable[[Iterator], Type[_ITEMS_T][_ITEM_T]]:
        """Make a converter for an iterator of items."""

        def wrapped(items: Iterator) -> Type[_ITEMS_T][_ITEM_T]:
            return items_converter(item_converter(item) for item in items)

        return wrapped

    @staticmethod
    def norm(
        converter: Callable | Type[_ITEM_T],
        klass: Type[_ITEM_T] = None,
    ) -> Callable[[Any], _ITEM_T]:
        """Make a converter skips values that are already converted."""

        def wrapped(value: Any) -> _ITEM_T:
            _klass = klass or converter
            if isinstance(value, _klass):
                return value

            return converter(value)

        return wrapped


class _BaseModel(BaseModel):
    _logger: ClassVar[Logger] = None

    def __init_subclass__(cls) -> None:
        cls._logger = getLogger(cls.__name__)
        return super().__init_subclass__()

    def dict(self, *args, **kwargs):
        kwargs["exclude_none"] = kwargs.get("exclude_none", True)
        kwargs["by_alias"] = kwargs.get("by_alias", True)
        return super().model_dump(*args, **kwargs)

    def json(self, *args, **kwargs):
        kwargs["exclude_none"] = kwargs.get("exclude_none", True)
        kwargs["by_alias"] = kwargs.get("by_alias", True)
        return super().model_dump_json(
            *args, **kwargs, exclude_none=True, by_alias=True
        )

    model_config = ConfigDict(extra="forbid")


class _RootListMixin(Generic[_VT]):
    def __len__(self) -> int:
        return len(self.__root__)

    def __iter__(self) -> Iterator[_VT]:
        return iter(self.__root__)

    def __getitem__(self, index: int) -> _VT:
        return self.__root__[index]

    def __setitem__(self, index: int, value: _VT) -> None:
        self.__root__[index] = value

    def append(self, value: _VT) -> None:
        self.__root__.append(value)

    def pop(self, index: int) -> _VT:
        return self.__root__.pop(index)

    def sort(self, *args, **kwargs) -> None:
        return self.__root__.sort(*args, **kwargs)


class _RootDictMixin(Generic[_KT, _VT]):
    def __len__(self) -> int:
        return len(self.__root__)

    """
    # TIL from ChatGPT
    If the __contains__ method doesn't exist, the interpreter falls back to iterating
    over the keys in the dict and checking if the given key is equal to any of them.
    This can be less efficient than using __contains__, especially for large
    dictionaries.
    """

    def __contains__(self, k: _KT) -> bool:
        return k in self.__root__

    def __iter__(self) -> Iterator[_KT]:
        return iter(self.__root__)

    def __getitem__(self, k: _KT) -> _VT:
        return self.__root__[k]

    def __setitem__(self, k: _KT, v: _VT) -> None:
        self.__root__[k] = v

    def keys(self) -> Iterator[_KT]:
        return self.__root__.keys()

    def values(self) -> Iterator[_VT]:
        return self.__root__.values()

    def items(self) -> Iterator[tuple[_KT, _VT]]:
        return self.__root__.items()

    def pop(self, k: _KT) -> _VT:
        return self.__root__.pop(k)

    def setdefault(self, k: _KT, default: _VT = None) -> _VT:
        return self.__root__.setdefault(k, default)
