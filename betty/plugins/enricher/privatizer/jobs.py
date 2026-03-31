"""
Jobs.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, override

from betty.job import Job
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.entity.person import Person
from betty.privacy import HasPrivacy

if TYPE_CHECKING:
    from collections.abc import MutableMapping, MutableSequence

    from betty.entity import Entity
    from betty.job.scheduler import Scheduler
    from betty.machine_name import MachineName
    from betty.project import Project
    from betty.typing import Intersection


class PrivatizeAncestry(Job):
    """
    Privatize an ancestry.
    """

    def __init__(self, dependencies: set[str] | None = None, *, project: Project):
        super().__init__(self.id_for(), dependencies=dependencies)
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "privatizer:privatize"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await self._project.upstream.localizer
        user = self._project.upstream.user

        newly_privatized: MutableMapping[MachineName, int] = defaultdict(lambda: 0)
        entities: MutableSequence[Intersection[HasPrivacy, Entity]] = []
        for entity in self._project.ancestry:
            if isinstance(entity, HasPrivacy):
                entities.append(entity)
                if entity.private:
                    newly_privatized[entity.plugin().id] -= 1

        for entity in entities:
            await self._project.privatizer.privatize(entity)

        for entity in entities:
            if entity.private:
                newly_privatized[entity.plugin().id] += 1

        if newly_privatized[Person.plugin().id] > 0:
            await user.message_information_details(
                _(
                    "Privatized {count} people because they are likely still alive."
                ).format(
                    count=str(newly_privatized[Person.plugin().id]),
                )
            )
        for entity_type_id in set(newly_privatized) - {Person.plugin().id}:
            if newly_privatized[entity_type_id] > 0:
                await user.message_information_details(
                    ngettext(
                        'Privatized {count} "{entity_type_id}" entity, because it is associated with private information.',
                        'Privatized {count} "{entity_type_id}" entities, because they are associated with private information.',
                        newly_privatized[entity_type_id],
                    ).format(
                        entity_type_id=entity_type_id,
                    )
                )
