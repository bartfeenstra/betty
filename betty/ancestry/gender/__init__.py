"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class Gender(Mutable, Plugin):
    """
    Define a gender.

    Read more about :doc:`/development/plugin/gender`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.gender.GenderTestBase`.
    """


GENDER_REPOSITORY: PluginRepository[Gender] = EntryPointPluginRepository("betty.gender")
"""
The gender plugin repository.

Read more about :doc:`/development/plugin/gender`.
"""
