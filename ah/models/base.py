from typing import ClassVar, Generic, Iterator, TypeVar

from logging import getLogger, Logger
from pydantic import BaseModel, Extra

__all__ = (
    "_BaseModel",
    "_BaseModelRootListMixin",
    "_BaseModelRootDictMixin",
)

_VT = TypeVar("_VT")
_KT = TypeVar("_KT")


class _BaseModel(BaseModel):
    _logger: ClassVar[Logger] = None

    def __init_subclass__(cls) -> None:
        cls._logger = getLogger(cls.__name__)
        return super().__init_subclass__()

    def dict(self, *args, **kwargs):
        kwargs["exclude_none"] = kwargs.get("exclude_none", True)
        kwargs["by_alias"] = kwargs.get("by_alias", True)
        return super().dict(*args, **kwargs)

    def json(self, *args, **kwargs):
        kwargs["exclude_none"] = kwargs.get("exclude_none", True)
        kwargs["by_alias"] = kwargs.get("by_alias", True)
        return super().json(*args, **kwargs, exclude_none=True, by_alias=True)

    class Config:
        extra = Extra.forbid
        use_enum_values = True


class _BaseModelRootListMixin(Generic[_VT]):
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


class _BaseModelRootDictMixin(Generic[_KT, _VT]):
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
