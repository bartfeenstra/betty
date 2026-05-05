"""
Object properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, cast, final, overload, override

from betty.datas.aggregate.record.object import Attr, AttrDefinition
from betty.functools import passthrough
from betty.importlib import fully_qualified_name
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.data import Data, DataDefinition
    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class Property[DataDefinitionT: DataDefinition, ValueGetT, ValueSetT](
    Attr[DataDefinitionT, ValueGetT]
):
    """
    An object attribute with a definition.
    """

    def __init__(
        self,
        data: Intersection[DataDefinition[ValueGetT], DataDefinitionT]
        | type[Data[Intersection[DataDefinition[ValueGetT], DataDefinitionT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[ValueGetT], bool] | None = None,
        resolver: Callable[[ValueSetT], ValueGetT] = passthrough,
        default: Callable[[], ValueGetT] | None = None,
    ):
        self._attr = AttrDefinition(
            data,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
        )
        # @todo Ideally we split these two out into new Property subclasses.
        # @todo Also the 'default subclass should use a lock for getting/creating a new value.
        self._default = default
        self._resolver = resolver

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.__name = f"_{name}"

    @final
    @property
    def name(self) -> str:
        """
        The attribute name.
        """
        return self.__name

    @final
    @override
    @property
    def attr(self) -> AttrDefinition[DataDefinitionT, ValueGetT]:
        return self._attr

    def get(self, instance: Any, /) -> ValueGetT:
        """
        Get the property value from the instance.
        """
        value = cast(
            ValueGetT | Void,
            getattr(instance, self.__name, Void),
        )
        if value is Void:
            if self._default is None:
                instance_name = fully_qualified_name(type(instance))
                raise PropertyNotInitialized(
                    f"{instance_name}.{self.__name[1:]} was never initialized. Either provide a default when initializing the property, or make {instance_name}.__init__() set a value."
                )
            value = self._default()
            setattr(instance, self.__name, value)
        return value  # ty:ignore[invalid-return-type]

    @overload
    def __get__(self, instance: None, owner: type[object], /) -> Self:
        pass

    @overload
    def __get__(self, instance: Any, owner: type[Any] | None = None, /) -> ValueGetT:
        pass

    @final
    def __get__(self, instance, owner=None, /):
        if instance is None:
            return self
        return self.get(instance)

    def set(self, instance: Any, value: ValueSetT, /) -> ValueGetT:
        """
        Set the value on the instance.
        """
        resolved_value = self._resolver(value)
        setattr(instance, self.__name, resolved_value)
        return resolved_value

    @final
    def __set__(self, instance: Any, value: ValueSetT | ValueGetT) -> None:
        self.set(instance, value)


@final
class PropertyNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.property.Property`.
    """
