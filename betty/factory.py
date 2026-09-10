"""
Object factories.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from inspect import iscoroutinefunction
from typing import Self, overload

from betty.asyncio import ResolvableAwaitable
from betty.callback import Arg1Callback, Arg2Callback, Callback, PreparedCallback


# @todo Raaaaaadical rethinking:
# @todo - What if we indeed make this a protocol (solving our inheritance issues).
# @todo - Rely on type checking only for enforcement. Class-based plugin definitions, for example, can use a
# @todo   bound on BaseClsT: ManufacturablePlugin, where ManufacturablePlugin = .....
# @todo   Anyway, the point is to check for compliance in the definitions, and the in the factory API assume that if
# @todo   a new() method is present (and the passed on value has passed the static type checks), we can try it as a
# @todo   callback like anything.
# @todo
# @todo BASICALLY: how much type checking do we want to do, and where?
# @todo
class Manufacturable[*ArgTs](metaclass=ABCMeta):
    """
    Allow this type to be initialized asynchronously.
    """

    @classmethod
    @abstractmethod
    async def new(cls, *args: *ArgTs) -> Self:
        """
        Create a new instance.
        """


type Manufacturer[T] = Callback[ResolvableAwaitable[T]]


type Arg1Manufacturer[T, Arg1T] = (
    type[Manufacturable[Arg1T]]
    | Arg1Callback[ResolvableAwaitable[T], Arg1T]
    | Manufacturer[T]
)


type Arg2Manufacturer[T, Arg1T, Arg2T] = (
    type[Manufacturable[Arg1T, Arg2T]]
    | Arg2Callback[ResolvableAwaitable[T], Arg1T, Arg2T]
)


@overload
async def new[T](manufacturer: Manufacturer[T], /) -> T:
    pass


@overload
async def new[T, Arg1T](manufacturer: Arg1Manufacturer[T, Arg1T], arg1: Arg1T, /) -> T:
    pass


@overload
async def new[T, Arg1T, Arg2T](
    manufacturer: Arg2Manufacturer[T, Arg1T, Arg2T], arg1: Arg1T, arg2: Arg2T, /
) -> T:
    pass


async def new(manufacturer, *args):
    """
    Create a new object from a manufacturer.
    """
    manufacturers = []
    if isinstance(manufacturer, type):
        if issubclass(manufacturer, Manufacturable):
            manufacturers.append(manufacturer.new)
        manufacturers.append(
            # Use a lambda to enforce a manufacturer with zero parameters, because we want to discourage dependency
            # injection into __int__().
            lambda: manufacturer(),  # noqa: PLW0108
        )
    bound_callback = PreparedCallback(*manufacturers).bind_value(*args)
    if iscoroutinefunction(bound_callback.callback):
        return await bound_callback()
    return bound_callback()
