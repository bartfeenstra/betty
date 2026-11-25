"""
Discover definitions within (sub)modules.
"""

from __future__ import annotations

import pathlib
from abc import ABCMeta, abstractmethod
from importlib import import_module
from inspect import getfile, getmembers, stack
from pkgutil import iter_modules, resolve_name
from typing import TYPE_CHECKING, Any, TypeGuard, final, override

from betty.definition import Definition, HasDefinition

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.service_level import ServiceLevel


class _ModuleDiscovery[DefinitionT: Definition]:
    @final
    def __init__(self, type_: type[DefinitionT], module: str | None = None, /):
        self._type = type_
        if module:
            self._module_name = module
            self._module = resolve_name(module)
        else:
            self._module_name = stack()[1].frame.f_globals["__name__"]
            self._module = import_module(self._module_name)
        self._module_path = pathlib.Path(getfile(self._module)).parent


class _ModuleMemberDiscovery[DefinitionT: Definition, MemberT](
    _ModuleDiscovery[DefinitionT], metaclass=ABCMeta
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
class ModuleDefinitionDiscovery[DefinitionT: Definition](
    _ModuleMemberDiscovery[DefinitionT, DefinitionT]
):
    """
    Discover definitions within a module.
    """

    @override
    def _is_discoverable(self, member: Any, /) -> TypeGuard[DefinitionT]:
        return isinstance(member, self._type)

    @override
    def _get_definition(self, member: DefinitionT, /) -> DefinitionT:
        return member


@final
class ModuleClsDiscovery[DefinitionT: Definition](
    _ModuleMemberDiscovery[DefinitionT, HasDefinition[DefinitionT]]
):
    """
    Discover classes within a module.
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
class SubmoduleClsDiscovery[DefinitionT: Definition](_ModuleDiscovery[DefinitionT]):
    """
    Discover definitions on classes within a module's submodules.
    """

    def __call__(self, _services: ServiceLevel, /) -> Iterator[DefinitionT]:
        """
        Discover the definitions.
        """
        for submodule in iter_modules([self._module_path]):
            if submodule.name.startswith("_"):
                continue
            yield from ModuleClsDiscovery(
                self._type, self._module_name + "." + submodule.name
            )(_services)
