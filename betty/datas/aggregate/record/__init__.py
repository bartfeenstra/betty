"""
Record data types.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Final, Self, final

from betty.collections import _empty_frozen_mapping
from betty.data import (
    DataDefinition,
    ResolvableDataDefinition,
    ResolvableDataPorter,
    Sample,
    Samples,
    resolve_data_definition,
)
from betty.indicator.operator import Attr, Key
from betty.localizable import resolve_localizable
from betty.portable.error import NotPortable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, MutableMapping

    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.nothing import NothingType
    from betty.portable import PortableData
    from betty.typing import Intersection


type FieldOperator = Attr | Key


class FieldPorter[OwnerT, DataT, FieldPorterLoadDataT = Any](metaclass=ABCMeta):
    """
    An object capable of dumping and loading field data to and from portable data.
    """

    @abstractmethod
    def dump(self, owner: OwnerT, data: DataT, /) -> PortableData | NothingType:
        """
        Dump data to its portable form.
        """

    @abstractmethod
    def load(self, data: PortableData, /) -> FieldPorterLoadDataT:
        """
        Load data from its portable form.
        """


type ResolvableFieldPorter[OwnerT, DataT] = (
    FieldPorter[OwnerT, DataT] | Callable[[FieldDefinition], FieldPorter[OwnerT, DataT]]
)


@final
class FieldDefinition[OwnerT, DataT, DataDefinitionT: DataDefinition = DataDefinition]:
    """
    A record field definition.
    """

    def __init__(
        self,
        data: ResolvableDataDefinition[
            Intersection[DataDefinitionT, DataDefinition[DataT]]
        ],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        optional: bool = False,
        porter: ResolvableFieldPorter[OwnerT, DataT] | None = None,
    ):
        from betty.porters.porter_field import PorterFieldPorter

        self.data: Final[DataDefinitionT] = resolve_data_definition(data)
        """
        The field's data definition.
        """

        self.label: Final[Localizable] = (
            self.data.label if label is None else resolve_localizable(label)
        )
        """
        The human-readable field label.
        """

        self.description: Final[Localizable | None] = (
            self.data.description
            if description is None
            else resolve_localizable(description)
        )
        """
        The human-readable long field description.
        """

        self.optional: Final[bool] = optional
        """
        Whether the field is optional within its enclosing record.
        """

        if porter is None:
            if data_porter := self.data.try_porter:
                porter = PorterFieldPorter(data_porter)
        elif not isinstance(porter, FieldPorter):
            porter = porter(self)
        self._porter: FieldPorter[OwnerT, DataT] = porter  # ty:ignore[invalid-assignment]

    @property
    def porter(self) -> FieldPorter[OwnerT, DataT]:
        """
        The porter for the data.
        """
        if self._porter is None:
            raise NotPortable(f"{self!r} does not have a porter.")
        return self._porter

    @property
    def try_porter(self) -> FieldPorter[OwnerT, DataT] | None:
        """
        The porter for the data, if it has one.
        """
        return self._porter


type ResolvableFieldDefinition[
    OwnerT,
    DataT,
    DataDefinitionT: DataDefinition = DataDefinition,
] = (
    FieldDefinition[OwnerT, DataT, DataDefinitionT]
    | ResolvableDataDefinition[DataDefinitionT]
)


def resolve_field_definition[OwnerT, DataT, DataDefinitionT: DataDefinition](
    field: ResolvableFieldDefinition[OwnerT, DataT, DataDefinitionT],
) -> FieldDefinition[OwnerT, DataT, DataDefinitionT]:
    """
    Resolve a value to a field definition.
    """
    if isinstance(field, FieldDefinition):
        return field
    return FieldDefinition(resolve_data_definition(field))


class RecordDefinition[DataT, OperatorT: FieldOperator](DataDefinition[DataT]):
    """
    A record data definition.

    Records have explicitly defined fields.
    """

    def __init__(
        self,
        *args: Any,
        cls: type[DataT] | None = None,
        label: ResolvableLocalizable,
        fields: Mapping[
            OperatorT, ResolvableFieldDefinition[DataT, Any]
        ] = _empty_frozen_mapping,
        description: ResolvableLocalizable | None = None,
        samples: Iterable[Callable[[], Sample[DataT]] | Samples] = (),
        factory: Callable[..., DataT] | None = None,
        porter: ResolvableDataPorter[Self, DataT] | None = None,
        **kwargs: Any,
    ):
        from betty.porters.fields import FieldsPorter

        self._factory = factory
        self._fields: MutableMapping[OperatorT, FieldDefinition[DataT, Any]] = {
            element: resolve_field_definition(field)
            for element, field in fields.items()
        }

        super().__init__(
            *args,
            cls=cls,
            label=label,
            description=description,
            samples=samples,
            porter=porter or FieldsPorter,
            **kwargs,
        )

    @property
    def factory(self) -> Callable[..., DataT]:
        """
        The factory to create new instances.

        The factory's arguments are kwargs whose names are this record's field names, and whose values are their fully
        typed values.
        """
        if self._factory:
            return self._factory
        if self.cls:
            return self.cls
        raise ValueError(
            "This definition does not have a factory. Either set a data class, or provide a factory when initializing the definition."
        )

    @property
    def fields(self) -> Mapping[OperatorT, FieldDefinition[DataT, Any]]:
        """
        The definitions of the fields contained by this record.
        """
        return self._fields
