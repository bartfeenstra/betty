"""
Key-value record data assertions.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING, Any, final

from betty.assertions import _HumanFacingValueError
from betty.assertions.mapping import assert_mapping
from betty.exception import reraise_with_indicator
from betty.indicator.selector import Key
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping

    from betty.functools import Pipe, Pipeline


@final
@dataclass(frozen=True)
class Field[ValueT, ReturnT]:
    """
    A key-value mapping field.
    """

    name: str
    assertion: Pipe[ValueT, ReturnT] | None = None
    _: KW_ONLY
    as_name: str | None = None
    optional: bool = False


def assert_record(
    *fields: Field[Any, Any], allow_extra: bool = False
) -> Pipeline[Any, MutableMapping[str, Any]]:
    """
    Assert that a value is a record: a key-value mapping of arbitrary value types, with a known structure.

    To validate a key-value mapping as a records, assertions for all possible keys
    MUST be provided. Any keys present in the value for which no field assertions
    are provided will cause the entire record assertion to fail.
    """

    def _assert_record(value: Mapping[Any, Any], /) -> MutableMapping[str, Any]:
        known_keys = {x.name for x in fields}
        unknown_keys = set(value.keys()) - known_keys
        record: MutableMapping[str, Any] = {}
        if not allow_extra:
            for unknown_key in unknown_keys:
                with reraise_with_indicator(Key(unknown_key)):
                    raise _HumanFacingValueError(
                        Paragraph(
                            _("Unknown key: {unknown_key}.").format(
                                unknown_key=f'"{unknown_key}"'
                            ),
                            do_you_mean(*(f'"{x}"' for x in sorted(known_keys))),
                        )
                    )
        for field in fields:
            with reraise_with_indicator(Key(field.name)):
                if field.name in value:
                    record[field.name if field.as_name is None else field.as_name] = (
                        field.assertion(value[field.name])
                        if field.assertion
                        else value[field.name]
                    )
                elif not field.optional:
                    raise _HumanFacingValueError(_("This field is required."))
        return record

    return assert_mapping() | _assert_record
