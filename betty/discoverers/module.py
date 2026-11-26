"""
Discover definitions within (sub)modules.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from inspect import getmembers
from pathlib import Path
from pkgutil import iter_modules, resolve_name
from typing import TYPE_CHECKING, Any, TypeGuard, final, override

from betty.definition import Definition, HasDefinition

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.service_level import ServiceLevel


class _ModuleDiscoverer[DefinitionT: Definition]:
    @final
    def __init__(self, type_: type[DefinitionT], module: str, /):
        self._type = type_
        self._module_name = module
        self._module = resolve_name(module)
        self._module_path = Path(self._module.__file__).parent


class _MemberDiscoverer[DefinitionT: Definition, MemberT](
    _ModuleDiscoverer[DefinitionT], metaclass=ABCMeta
):
    @final
    def __call__(self, _services: ServiceLevel, /) -> Iterator[DefinitionT]:
        """
        Discover the definitions.
        """
        for name, member in getmembers(self._module, self._is_discoverable):
            if not name.startswith("_"):
                yield self._get_definition(member)

    @abstractmethod
    def _is_discoverable(self, member: Any, /) -> TypeGuard[MemberT]:
        pass

    @abstractmethod
    def _get_definition(self, member: MemberT, /) -> DefinitionT:
        pass


@final
class DefinitionDiscoverer[DefinitionT: Definition](
    _MemberDiscoverer[DefinitionT, DefinitionT]
):
    """
    Discover :py:class:`betty.definition.Definition` instances  within a module.
    """

    @override
    def _is_discoverable(self, member: Any, /) -> TypeGuard[DefinitionT]:
        return isinstance(member, self._type)

    @override
    def _get_definition(self, member: DefinitionT, /) -> DefinitionT:
        return member


@final
class HasDefinitionDiscoverer[DefinitionT: Definition](
    _MemberDiscoverer[DefinitionT, HasDefinition[DefinitionT]]
):
    """
    Discover :py:class:`betty.definition.HasDefinition` instances  within a module.
    """

    @override
    def _is_discoverable(self, member: Any, /) -> TypeGuard[HasDefinition[DefinitionT]]:
        if not isinstance(member, type):
            return False
        if getattr(member, "__module__", None) != self._module.__name__:
            return False
        if not issubclass(member, HasDefinition):
            return False
        return isinstance(
            # Base classes don't actually have their own definition.
            getattr(member, "definition", None),
            self._type,
        )

    @override
    def _get_definition(self, member: HasDefinition[DefinitionT], /) -> DefinitionT:
        return member.definition


@final
class SubmoduleHasDefinitionDiscoverer[DefinitionT: Definition](
    _ModuleDiscoverer[DefinitionT]
):
    """
    Discover :py:class:`betty.definition.Definition` instances  within a module's submodules.
    """

    def __call__(self, _services: ServiceLevel, /) -> Iterator[DefinitionT]:
        """
        Discover the definitions.
        """
        for submodule in iter_modules([self._module_path]):
            if submodule.name.startswith("_"):
                continue
            yield from HasDefinitionDiscoverer(
                self._type, self._module_name + "." + submodule.name
            )(_services)
