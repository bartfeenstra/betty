"""
The subject role.
"""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "subject",
    label=_("Subject"),
    label_plural=_("Subjects"),
    label_countable=ngettext("{count} subjects", "{count} subjects"),
)
class Subject(Role):
    """
    .. plugin:: role:subject.

    The meaning of this role depends on the event type. For example, for
    :py:class:`betty.event_types.marriage.Marriage`, the subjects are the people who got married. For
    :py:class:`betty.event_types.death.Death` it is the person who died.
    """
