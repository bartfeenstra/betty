"""
Machine names.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final, Self, final
from uuid import uuid4

from betty.data import Data, DataDefinition
from betty.functools import passthrough, raise_
from betty.localizables.gettext import _
from betty.porters.callback import CallbackPorter
from betty.validation import Invalid
from betty.validators.str import is_str, is_str_max_len, is_str_min_len

if TYPE_CHECKING:
    from betty.localizable import Localizable

machine_name_description: Final[Localizable] = _(
    "An identifier of at most 250 characters long, made up of lowercase letters, numbers, and/or non-consecutive hyphens (-)."
)
__disallowed_character_pattern = r"[^a-z0-9\-]"
__disallowed_hyphen_pattern = "--+"
_disallowed_hyphen_pattern = re.compile(__disallowed_hyphen_pattern)
_disallowed_character_pattern = re.compile(__disallowed_character_pattern)
_disallowed_pattern = re.compile(
    __disallowed_character_pattern + "|" + __disallowed_hyphen_pattern
)
_disallowed_message = _(
    "This must consist of lowercase letters, numbers, and/or non-consecutive hyphens (-)."
)
_validate = (
    is_str_min_len(1)
    | is_str_max_len(250)
    | (
        lambda value: (
            raise_(Invalid(value, _disallowed_message))
            if _disallowed_pattern.search(value)
            else value
        )
    )
)


@final
@DataDefinition(
    label=_("Machine name"),
    description=machine_name_description,
    porter=lambda _: CallbackPorter(is_str | MachineName, passthrough),
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

    def __new__(cls, machine_name: str | None = None, /):
        """
        Create a new instance, or return existing machine names unchanged.
        """
        if isinstance(machine_name, cls):
            return machine_name
        if machine_name is None:
            persistent = False
            machine_name = str(uuid4())
        else:
            _validate(machine_name)
            persistent = True
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
    def machinify(cls, source: str, /) -> Self | None:
        """
        Attempt to convert a source string into a valid machine name.
        """
        machine_name = (
            _disallowed_hyphen_pattern.sub(
                "-",
                (
                    _disallowed_character_pattern.sub("-", source.lower()).strip("-")[
                        :250
                    ]
                ),
            )
            or None
        )
        if machine_name is None:
            return None
        return cls(machine_name)


type ResolvableMachineName = MachineName | str
