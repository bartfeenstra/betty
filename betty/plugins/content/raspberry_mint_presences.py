"""
The presences content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.data import Data
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName
from betty.plugin import ResolvablePluginId, resolve_plugin_id
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.event import Event
from betty.project import Project
from betty.property import Optional, Property
from betty.requirement import require
from betty.role import RoleDefinition
from betty.sample import Sample, Size
from betty.service.factory import DataManufacturable, Manufacturable

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.jinja import Environment


@final
@ObjectDefinition(
    label=_("Presences configuration"),
    samples=[
        lambda: Sample(PresencesConfiguration(), label="Minimal"),
        lambda: Sample(
            PresencesConfiguration(include=["subject"]),
            label="Includes",
            size=Size.FULL,
        ),
        lambda: Sample(
            PresencesConfiguration(exclude=["subject"]),
            label="Excludes",
            size=Size.FULL,
        ),
    ],
)
class PresencesConfiguration(Data):
    """
    Configuration for :py:class:`betty.plugins.content.raspberry_mint_presences.Presences`.

    .. data:: betty.plugins.content.raspberry_mint_presences:PresencesConfiguration
    """

    exclude = Optional(
        Property(SequenceDefinition(cls=list, value=MachineName, label=_("Exclude")))
    )
    """
    The presence roles for which to exclude presences.
    """

    include = Optional(
        Property(SequenceDefinition(cls=list, value=MachineName, label=_("Include")))
    )
    """
    The presence roles for which to include presences.
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvablePluginId[RoleDefinition]] | None = None,
        exclude: Iterable[ResolvablePluginId[RoleDefinition]] | None = None,
    ):
        super().__init__()
        if include is not None:
            self.include = list(map(resolve_plugin_id, include))
        if exclude is not None:
            self.exclude = list(map(resolve_plugin_id, exclude))


@final
@ContentDefinition("raspberry-mint-presences", label=_("Presences"))
class Presences(Template, DataManufacturable[PresencesConfiguration], Manufacturable):
    """
    People's presences at an event.

    .. plugin:: content:raspberry-mint-presences
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvablePluginId[RoleDefinition]] | None = None,
        jinja: Environment,
    ):
        super().__init__(jinja=jinja)
        self._include = (
            None if include is None else tuple(map(resolve_plugin_id, include))
        )

    @override
    @classmethod
    def new_data_cls(cls) -> type[PresencesConfiguration]:
        return PresencesConfiguration

    @override
    @classmethod
    @require(Project)
    async def new(
        cls, project: Project, data: PresencesConfiguration | None = None, /
    ) -> Self:

        if data is None:
            raise NotImplementedError
        include: Iterable[ResolvablePluginId[RoleDefinition]] | None
        if data.include is not None:
            include = data.include
        else:
            roles = project.plugins[RoleDefinition]
            include = {role.id async for role in roles}
            if data.exclude is not None:
                include -= set(data.exclude)
        return cls(include=include, jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Event):
            presences = document.resource.presences
            if self._include is not None:
                presences = tuple(
                    presence
                    for presence in presences
                    if presence.role.plugin().id in self._include
                )
            if not len(presences):
                return None
            return "component/raspberry-mint/presences.html.j2", {
                "presences": presences
            }
        return None
