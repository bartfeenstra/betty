"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations


from betty.locale.localizable import _
from betty.plugin import Plugin, PluginRepository, PluginShorthandBase
from betty.plugin.entry_point import EntryPointPluginRepository


class Gender(Plugin):
    """
    Define a gender.

    Read more about :doc:`/development/plugin/gender`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.gender.GenderTestBase`.
    """

    pass


GENDER_REPOSITORY: PluginRepository[Gender] = EntryPointPluginRepository("betty.gender")
"""
The gender plugin repository.

Read more about :doc:`/development/plugin/gender`.
"""


class NonBinary(PluginShorthandBase, Gender):
    """
    A non-binary person.
    """

    _plugin_id = "non-binary"
    _plugin_label = _("Non-binary")


class Female(PluginShorthandBase, Gender):
    """
    A female person.
    """

    _plugin_id = "female"
    _plugin_label = _("Female")


class Male(PluginShorthandBase, Gender):
    """
    A male person.
    """

    _plugin_id = "male"
    _plugin_label = _("Male")


class Unknown(PluginShorthandBase, Gender):
    """
    A person of an unknown gender.
    """

    _plugin_id = "unknown"
    _plugin_label = _("Unknown")
