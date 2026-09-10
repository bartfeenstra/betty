"""
The presences content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.attrs.owner import OwnerAttr
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.datas.aggregate.collection.list import ListDefinition
from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition.id import resolve_id
from betty.entities.event import Event
from betty.localizables.gettext import _
from betty.machine_name import MachineName
from betty.plugin.config.factory import ConfigurableIntegratable
from betty.project import Project
from betty.role import RoleDefinition
from betty.sample import Sample, Samples, Size
from betty.service_level.factory import Integratable

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.definition.id import ResolvableId
    from betty.document import Document
    from betty.jinja import Environment


@final
@ObjectDefinition(
    label=_("Presences configuration"),
    samples=Samples(
        lambda: Sample(PresencesConfig(), label="Minimal"),
        lambda: Sample(
            PresencesConfig(include=["subject"]),
            label="Includes",
            size=Size.FULL,
        ),
        lambda: Sample(
            PresencesConfig(exclude=["subject"]),
            label="Excludes",
            size=Size.FULL,
        ),
    ),
)
class PresencesConfig(Object):
    """
    Configuration for :py:class:`betty.content_builders.raspberry_mint_presences.Presences`.

    .. data:: betty.content_builders.raspberry_mint_presences:PresencesData
    """

    exclude = OwnerAttr(ListDefinition(value=MachineName, label=_("Exclude"))).optional
    """
    The presence roles for which to exclude presences.
    """

    include = OwnerAttr(ListDefinition(value=MachineName, label=_("Include"))).optional
    """
    The presence roles for which to include presences.
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvableId[RoleDefinition]] | None = None,
        exclude: Iterable[ResolvableId[RoleDefinition]] | None = None,
    ):
        super().__init__()
        if include is not None:
            self.include = list(map(resolve_id, include))
        if exclude is not None:
            self.exclude = list(map(resolve_id, exclude))


@final
@ContentBuilderDefinition(
    "raspberry-mint-presences",
    label=_("Presences"),
    config_cls=PresencesConfig,
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Presences(Template, ConfigurableIntegratable[PresencesConfig], Integratable):
    """
    People's presences at an event.

    .. plugin:: content-builder:raspberry-mint-presences
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvableId[RoleDefinition]] | None = None,
        jinja: Environment,
    ):
        super().__init__(jinja=jinja)
        self._include = None if include is None else tuple(map(resolve_id, include))

    @override
    @Project.require
    @classmethod
    async def new(
        cls, project: Project, config: PresencesConfig | None = None, /
    ) -> Self:

        if config is None:
            raise NotImplementedError
        include: Iterable[ResolvableId[RoleDefinition]] | None
        if config.include is not None:
            include = config.include
        else:
            roles = project.plugins[RoleDefinition]
            include = {role.id async for role in roles}
            if config.exclude is not None:
                include -= set(config.exclude)
        return cls(include=include, jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Event):
            presences = document.resource.presences
            if self._include is not None:
                presences = tuple(
                    presence
                    for presence in presences
                    if presence.role.definition.id in self._include
                )
            if not presences:
                return None
            return "component/raspberry-mint/presences.html.j2", {
                "presences": presences
            }
        return None
