"""
Provide concrete gender implementations.
"""

from typing import final

from betty.ancestry.gender import Gender, GenderDefinition
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@GenderDefinition(
    id="female",
    label=_("Female"),
)
class Female(Gender):
    """
    A female person.
    """


@final
@GenderDefinition(
    id="male",
    label=_("Male"),
)
class Male(Gender):
    """
    A male person.
    """


@final
@GenderDefinition(
    id="non-binary",
    label=_("Non-binary"),
)
class NonBinary(Gender):
    """
    A non-binary person.
    """


@final
@GenderDefinition(
    id="unknown",
    label=_("Unknown"),
)
class Unknown(Gender, Singleton):
    """
    A person of an unknown gender.
    """
