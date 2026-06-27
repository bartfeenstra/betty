"""
Object data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, override

from betty.attr import Attr
from betty.datas.aggregate.record import FieldDefinition, RecordDefinition
from betty.indicator.selector import Attr as AttrElement
from betty.portable import Porter
from betty.prop import HasProps

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from betty.data import ResolvableDataDefinitionFeature
    from betty.localizable import ResolvableLocalizable
    from betty.sample import Sample, Samples
    from betty.typing import Intersection


class ObjectDefinition[DataT, PorterT: Porter = Porter](
    RecordDefinition[DataT, PorterT, AttrElement]
):
    """
    Define an object with attributes.

    Use :py:class:`betty.attr.Attr` to define fields inline, or in superclasses so they can be inherited.
    """

    def __init__(
        self,
        *args: Any,
        cls: type[DataT] | None = None,
        label: ResolvableLocalizable,
        fields: Mapping[AttrElement | str, FieldDefinition[DataT, Any]] | None = None,
        description: ResolvableLocalizable | None = None,
        samples: Iterable[Callable[[], Sample[DataT]] | Samples] = (),
        factory: Callable[..., DataT] | None = None,
        porter: ResolvableDataDefinitionFeature[
            Intersection[PorterT, Porter[DataT]], Self, DataT
        ]
        | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            *args,
            cls=cls,
            label=label,
            description=description,
            factory=factory,
            fields=None
            if fields is None
            else {
                name if isinstance(name, AttrElement) else AttrElement(name): field
                for name, field in fields.items()
            },
            samples=samples,
            porter=porter,
            **kwargs,
        )

    @override
    def _set_cls(self, cls: type[DataT], /) -> None:
        if issubclass(cls, HasProps):
            for prop in cls.props():
                if isinstance(prop, Attr):
                    self._fields[AttrElement(prop.prop.name)] = prop.field
        super()._set_cls(cls)
