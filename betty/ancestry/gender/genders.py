"""
Provide concrete gender implementations.
"""

from betty.ancestry.gender import Gender
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase


class Female(ShorthandPluginBase, Gender):
    """
    A female person.
    """

    _plugin_id = "female"
    _plugin_label = _("Female")


class Male(ShorthandPluginBase, Gender):
    """
    A male person.
    """

    _plugin_id = "male"
    _plugin_label = _("Male")


class NonBinary(ShorthandPluginBase, Gender):
    """
    A non-binary person.
    """

    _plugin_id = "non-binary"
    _plugin_label = _("Non-binary")


class Unknown(ShorthandPluginBase, Gender):
    """
    A person of an unknown gender.
    """

    _plugin_id = "unknown"
    _plugin_label = _("Unknown")
