"""
The negotiation API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Final, final, override

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from ty_extensions import Not


class Negotiator[
    KeyT,
    ResolvableKeyT,
    MatchT: Not[None],
    UnsupportedT: Exception,
](metaclass=ABCMeta):
    """
    Negotiate the best match against available targets.
    """

    __slots__ = ()

    @abstractmethod
    def _new_unsupported(self, key: ResolvableKeyT | KeyT, /) -> UnsupportedT:
        """
        Create a new error for an unsupported key.
        """

    @abstractmethod
    def request(self, other: ResolvableKeyT | KeyT, /) -> MatchT | None:
        """
        Request a match by a key.
        """

    @final
    def require(self, other: ResolvableKeyT | KeyT, /) -> MatchT:
        """
        Require a match by a key.
        """
        if match := self.request(other):
            return match
        raise self._new_unsupported(other)


class MappingNegotiator[
    KeyT,
    ResolvableKeyT,
    MatchT: Not[None],
    UnsupportedT: Exception,
    ValueT,
](Negotiator[KeyT, ResolvableKeyT, MatchT, UnsupportedT]):
    """
    A negotiator backed by a mapping.
    """

    __slots__ = ("__match", "_resolve", "_values")

    def __init__(
        self,
        keyer: Callable[[ValueT], Iterable[KeyT]],
        matcher: Callable[[ValueT], MatchT],
        resolver: Callable[[ResolvableKeyT | KeyT], KeyT],
        /,
        *values: ValueT,
    ):
        self.__match = matcher
        self._resolve: Final[Callable[[ResolvableKeyT | KeyT], KeyT]] = resolver
        self._values: Final[Mapping[KeyT, ValueT]] = {
            key: target for target in reversed(values) for key in keyer(target)
        }

    @final
    @override
    def request(self, other: ResolvableKeyT | KeyT, /) -> MatchT | None:
        other = self._resolve(other)
        target = self._values.get(other, None)
        if target is None:
            return None
        return self.__match(target)
