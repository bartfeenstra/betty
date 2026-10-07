"""
Key-value record data validators.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING, Any, final

from betty.localizables.gettext import _
from betty.localizables.markup import do_you_mean
from betty.operator import Key
from betty.validation import Invalid, Validator, collect
from betty.validators.mapping import is_mapping

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.functools import Pipe


@final
class UnknownField(Invalid):
    """
    Raised when validating an unknown field.
    """


@final
class MissingField(Invalid):
    """
    Raised when a required field is missing.
    """


@final
@dataclass(frozen=True)
class Field[ValueT, ReturnT]:
    """
    A key-value mapping field.
    """

    name: str
    validator: Validator[ValueT, ReturnT] | None = None
    _: KW_ONLY
    optional: bool = False


def is_record(
    *fields: Field[Any, Any], allow_extra: bool = False
) -> Pipe[Any, Mapping[str, Any]]:
    """
    Validate that a value is a record: a key-value mapping of arbitrary value types, with a known structure.

    To validate a key-value mapping as a records, validators for all possible keys
    MUST be provided. Any keys present in the value for which no field validators
    are provided will cause the entire record validator to fail.
    """

    def _is_record(value: Mapping[Any, Any], /) -> Mapping[str, Any]:
        known_keys = {x.name for x in fields}
        unknown_keys = set(value.keys()) - known_keys
        record: dict[str, Any] = {}
        with collect(value) as errors:
            if not allow_extra:
                for unknown_key in unknown_keys:
                    errors.add(
                        UnknownField(
                            value,
                            _("This field is unknown.").format(
                                unknown_key=f'"{unknown_key}"'
                            ),
                            hint=do_you_mean(*(f'"{x}"' for x in sorted(known_keys))),
                            location=[Key(unknown_key)],
                        )
                    )
            for field in fields:
                if field.name in value:
                    record[field.name] = (
                        field.validator(value[field.name])
                        if field.validator
                        else value[field.name]
                    )
                elif not field.optional:
                    errors.add(
                        MissingField(
                            value,
                            _("This field is required."),
                            location=[Key(field.name)],
                        )
                    )
        return record

    return is_mapping | _is_record
