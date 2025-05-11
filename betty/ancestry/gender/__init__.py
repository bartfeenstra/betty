"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import Localizable, _
from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from betty.machine_name import MachineName


class Gender(Mutable, Plugin):
    """
    Define a gender.

    Read more about :doc:`/development/plugin/gender`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.gender.GenderTestBase`.
    """

    @final
    @override
    @classmethod
    def plugin_type_cls(cls) -> type[Plugin]:
        return Gender

    @final
    @override
    @classmethod
    def plugin_type_id(cls) -> MachineName:
        return "gender"

    @final
    @override
    @classmethod
    def plugin_type_label(cls) -> Localizable:
        return _("Gender")


GENDER_REPOSITORY: PluginRepository[Gender] = EntryPointPluginRepository(
    Gender, "betty.gender"
)
"""
The gender plugin repository.

Read more about :doc:`/development/plugin/gender`.
"""
