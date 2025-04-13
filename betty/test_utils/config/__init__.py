"""
Test utilities for :py:mod:`betty.config`.
"""

from typing import Any

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    assert_none,
    assert_or,
    assert_record,
    assert_setattr,
    assert_str,
)
from betty.config import Configuration
from betty.serde.dump import Dump


class DummyConfiguration(Configuration):
    """
    A dummy :py:class:`betty.config.Configuration` implementation.
    """

    def __init__(self, value: str | None = None, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.value = value

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField(
                "value",
                assert_or(assert_none(), assert_str()) | assert_setattr(self, "value"),
            )
        )(dump)

    @override
    def dump(self) -> Dump:
        if self.value is None:
            return {}
        return {
            "value": self.value,
        }
