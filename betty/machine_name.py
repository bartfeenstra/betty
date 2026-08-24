"""
Machine names.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final, Self, final, override
from uuid import uuid4

from betty.assertions.str import assert_str
from betty.data import Data, DataDefinition
from betty.exception import HumanFacingException
from betty.functools import passthrough
from betty.indexers.str import StrIndexer
from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph, Quote
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizable import Localizable
    from betty.portable import PortableData

machine_name_description: Final[Localizable] = _(
    "A machine name is an identifier of at most 250 characters long, made up of lowercase letters, numbers, and/or non-consecutive hyphens (-)."
)
_machine_name_pattern: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9\-]{1,250}$")
_machinify_disallowed_character_pattern: Final[re.Pattern[str]] = re.compile(
    r"[^a-z0-9\-]"
)
_machinify_hyphen_pattern: Final[re.Pattern[str]] = re.compile(r"-{2,}")

__load = assert_str()


def _load(portable: PortableData, /) -> MachineName:
    return MachineName(__load(portable))


@final
@DataDefinition(
    label=_("Machine name"),
    description=machine_name_description,
    indexer=StrIndexer(),
    porter=CallbackPorter(_load, passthrough),
)
class MachineName(str, Data):
    """
    A machine name.

    A machine name is a string that meets these criteria:
    - At least 1 character long.
    - At most 250 characters long.
    - Lowercase letters, numbers, and non-consecutive hyphens (-).
    """

    __slots__ = ("_persistent",)

    _persistent: bool

    @override
    def __new__(cls, machine_name: str | None = None, /):
        if machine_name is None:
            machine_name = str(uuid4())
            persistent = False
        else:
            persistent = True
            if (
                _machine_name_pattern.fullmatch(machine_name) is None
                or "--" in machine_name
            ):
                raise InvalidMachineName(machine_name)
        new = super().__new__(cls, machine_name)
        new._persistent = persistent
        return new

    def __init__(self, machine_name: str | None = None, /):
        pass

    @property
    def persistent(self) -> bool:
        """
        Whether this machine name is persistent, and will exist beyond the current Betty process.
        """
        return self._persistent

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
                _("{value} is not a valid machine name.").format(value=Quote(value)),
                machine_name_description,
            )
        )
