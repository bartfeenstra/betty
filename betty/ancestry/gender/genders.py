"""
Provide concrete gender implementations.
"""

from typing import final

from betty.ancestry.gender import Gender, GenderPlugin
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@GenderPlugin(
    id="female",
    label=_("Female"),
)
class Female(Gender):
    """
    A female person.
    """


@final
@GenderPlugin(
    id="male",
    label=_("Male"),
)
class Male(Gender):
    """
    A male person.
    """


@final
@GenderPlugin(
    id="non-binary",
    label=_("Non-binary"),
)
class NonBinary(Gender):
    """
    A non-binary person.
    """


@final
@GenderPlugin(
    id="unknown",
    label=_("Unknown"),
)
class Unknown(Gender, Singleton):
    """
    A person of an unknown gender.
    """
