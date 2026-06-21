"""
The beneficiary role.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "beneficiary",
    label=_("Beneficiary"),
    label_plural=_("Beneficiaries"),
    label_countable=ngettext("{count} beneficiary", "{count} beneficiaries"),
)
class Beneficiary(Role):
    """
    .. plugin:: role:beneficiary.

    Someone was a `benificiary <https://en.wikipedia.org/wiki/Beneficiary>`_ in the event, such as a
    :py:class:`betty.event_types.will.Will`.
    """
