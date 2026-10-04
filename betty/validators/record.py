"""
Key-value record data validators.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING, Any, final

from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph, do_you_mean
from betty.locator.operator import Key
from betty.validation import Invalid, Validator, group, locate
from betty.validators.mapping import is_mapping

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.functools import Pipeline


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
) -> Pipeline[Any, Mapping[str, Any]]:
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
        if not allow_extra:
            for unknown_key in unknown_keys:
                with locate(Key(unknown_key)), group():
                    raise Invalid(
                        Paragraph(
                            _("Unknown key: {unknown_key}.").format(
                                unknown_key=f'"{unknown_key}"'
                            ),
                            do_you_mean(*(f'"{x}"' for x in sorted(known_keys))),
                        )
                    )
        for field in fields:
            with locate(Key(field.name)), group():
                if field.name in value:
                    record[field.name] = (
                        field.validator(value[field.name])
                        if field.validator
                        else value[field.name]
                    )
                elif not field.optional:
                    raise Invalid(_("This field is required."))
        return record

    return is_mapping() | _is_record
