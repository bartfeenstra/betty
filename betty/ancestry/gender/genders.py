"""
Provide concrete gender implementations.
"""

from typing import final

from betty.ancestry.gender import Gender, GenderDefinition
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@GenderDefinition("female", label=_("Female"))
class Female(Gender):
    """
    A female person.
    """


@final
@GenderDefinition("male", label=_("Male"))
class Male(Gender):
    """
    A male person.
    """


@final
@GenderDefinition("non-binary", label=_("Non-binary"))
class NonBinary(Gender):
    """
    A non-binary person.
    """


@final
@GenderDefinition("unknown", label=_("Unknown"))
class Unknown(Gender, Singleton):
    """
    A person of an unknown gender.
    """
