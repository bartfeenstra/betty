"""
Data that has human-readable descriptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attr import Object
from betty.attrs.localizable import new_localizable_attr
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


class HasDescription[DataDefinitionT: ObjectDefinition = ObjectDefinition](
    Object[DataDefinitionT]
):
    """
    Data with a description.
    """

    description = new_localizable_attr(label=_("Description")).optional
    """
    The description.
    """

    def __init__(
        self,
        *args: Any,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description
