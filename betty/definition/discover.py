"""
Discover definitions.
"""

from __future__ import annotations

from asyncio import gather
from collections.abc import Callable, Iterable
from contextlib import suppress
from itertools import chain

from betty.asyncio import ResolvableAwaitable, resolve_await
from betty.definition import (
    Definition,
    HasDefinition,
    ResolvableDefinition,
)
from betty.requirement import UnmetRequirement
from betty.service_level import ServiceLevel
from betty.typing import RuntimeCheckableSequence, is_runtime_checkable_sequence

type Discovery[DefinitionT: Definition = Definition] = (
    ResolvableDefinition[DefinitionT]
    | RuntimeCheckableSequence[Discovery[DefinitionT]]
    | Callable[[ServiceLevel], ResolvableAwaitable[Iterable[Discovery[DefinitionT]]]]
)


async def discover[DefinitionT: Definition](
    services: ServiceLevel, /, *discoveries: Discovery[DefinitionT]
) -> Iterable[DefinitionT]:
    """
    Discover definitions.
    """
    return chain(
        *await gather(*[_discover(discovery, services) for discovery in discoveries])
    )


async def _discover[DefinitionT: Definition](
    discovery: Discovery[DefinitionT], services: ServiceLevel, /
) -> Iterable[DefinitionT]:
    if isinstance(discovery, Definition):
        return (discovery,)  # ty: ignore[invalid-return-type]
    if isinstance(discovery, type) and issubclass(discovery, HasDefinition):
        return (discovery.definition,)
    if is_runtime_checkable_sequence(discovery):
        return await discover(services, *discovery)
    with suppress(UnmetRequirement):
        return await discover(services, *await resolve_await(discovery(services)))
    return ()
