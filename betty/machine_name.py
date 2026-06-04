"""
Machine names.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final, Self, final, override

from betty.assertions.str import assert_str
from betty.data import Data, DataDefinition
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph
from betty.portable import Portable, PortableData

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable

_machine_name_description: Final[Localizable] = _(
    "A machine name is an identifier of at most 250 characters long, made up of lowercase letters, numbers, and/or hyphens (-)."
)
_machine_name_pattern: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9\-]{1,250}$")
_machinify_disallowed_character_pattern: Final[re.Pattern[str]] = re.compile(
    r"[^a-z0-9\-]"
)
_machinify_hyphen_pattern: Final[re.Pattern[str]] = re.compile(r"-{2,}")


@final
@DataDefinition(label=_("Machine name"))
class MachineName(Portable[str], str, Data):
    """
    A machine name.

    A machine name is a string that meets these criteria:
    - At most 250 characters long.
    - Lowercase letters, numbers, and hyphens (-).
    """

    __slots__ = ()

    @override
    def __new__(cls, machine_name: str, /):
        if _machine_name_pattern.fullmatch(machine_name) is None:
            raise InvalidMachineName(machine_name)
        return super().__new__(cls, machine_name)

    def __init__(self, machine_name: str, /):
        pass

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(assert_str()(portable))

    @override
    def dump(self) -> str:
        return self

    @classmethod
    def resolve(cls, machine_name: ResolvableMachineName) -> MachineName:
        """
        Resolve a value to a machine name.
        """
        if isinstance(machine_name, cls):
            return machine_name
        return cls(machine_name)

    @classmethod
    def machinify(cls, source: str, /) -> Self | None:
        """
        Attempt to convert a source string into a valid machine name.
        """
        machine_name = (
            _machinify_hyphen_pattern.sub(
                "-", _machinify_disallowed_character_pattern.sub("-", source.lower())
            ).strip("-")[:250]
            or None
        )
        if machine_name is None:
            return None
        return cls(machine_name)


type ResolvableMachineName = MachineName | str


@final
class InvalidMachineName(HumanFacingException, ValueError):
    """
    Raised when something is not a valid machine name.
    """

    def __init__(self, value: str, /):
        super().__init__(
            Paragraph(
                _('"{value}" is not a valid machine name.').format(value=value),
                _machine_name_description,
            )
        )
