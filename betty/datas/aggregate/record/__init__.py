"""
Record data types.
"""

from __future__ import annotations

from inspect import signature
from typing import TYPE_CHECKING, Any, Final, Self, final

from betty.data import (
    DataDefinition,
    ResolvableDataDefinition,
    ResolvableDataDefinitionManufacturable,
    Sample,
    Samples,
    resolve_data_definition,
)
from betty.indicator.selector import Element
from betty.localizable import resolve_localizable
from betty.portable import Porter
from betty.porters.fields import FieldsPorter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, MutableMapping

    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.typing import Intersection


@final
class FieldDefinition[
    OwnerT,
    DataClsT,
    DataDefinitionT: DataDefinition = DataDefinition,
]:
    """
    A record field definition.
    """

    def __init__(
        self,
        data: ResolvableDataDefinition[
            Intersection[DataDefinitionT, DataDefinition[DataClsT]]
        ],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool = False,
        omit_dump: Callable[[DataClsT], bool]
        | Callable[[OwnerT, DataClsT], bool]
        | None = None,
    ):
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

        self.omit_load: Final[bool] = omit_load
        """
        Whether the field may be omitted from the parent when loading from portable data.
        """

        self._omit_dump: Callable[[OwnerT, DataClsT], bool] | None = (
            None
            if omit_dump is None
            else (
                (
                    lambda _, data: omit_dump(
                        data,  # ty:ignore[invalid-argument-type]
                    )  # ty:ignore[missing-argument]
                )
                if len(signature(omit_dump).parameters) == 1
                else omit_dump
            )  # ty:ignore[invalid-assignment]
        )

    def omit_dump(self, owner: OwnerT, data: DataClsT, /) -> bool:
        """
        Check if the field may be omitted from the parent when dumping to portable data.
        """
        if self._omit_dump is None:
            return False
        return self._omit_dump(owner, data)


class RecordDefinition[
    DataClsT,
    PorterT: Porter = Porter,
    ElementT: Element[str] = Element[str],
](DataDefinition[DataClsT, PorterT]):
    """
    A record data definition.

    Records have explicitly defined fields.
    """

    def __init__(
        self,
        *args: Any,
        cls: type[DataClsT] | None = None,
        label: ResolvableLocalizable,
        fields: Mapping[ElementT, FieldDefinition[DataClsT, Any]] | None = None,
        description: ResolvableLocalizable | None = None,
        samples: Iterable[Callable[[], Sample[DataClsT]] | Samples] = (),
        factory: Callable[..., DataClsT] | None = None,
        porter: ResolvableDataDefinitionManufacturable[
            Intersection[PorterT, Porter[DataClsT]], Self, DataClsT
        ]
        | None = None,
        **kwargs: Any,
    ):
        self._factory = factory
        self._fields: MutableMapping[ElementT, FieldDefinition[DataClsT, Any]] = (
            {} if fields is None else dict(fields)
        )

        super().__init__(
            *args,
            cls=cls,
            label=label,
            description=description,
            samples=samples,
            porter=porter or (lambda record, __: FieldsPorter(record)),
            **kwargs,
        )

    @property
    def factory(self) -> Callable[..., DataClsT]:
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
    def fields(self) -> Mapping[ElementT, FieldDefinition[DataClsT, Any]]:
        """
        The definitions of the fields contained by this record.
        """
        return self._fields
