"""
Test utilities for :py:mod:`betty.config`.
"""

from typing import Self

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    assert_none,
    assert_or,
    assert_record,
    assert_str,
)
from betty.config import Configurable, Configuration
from betty.serde.dump import Dump


class DummyConfiguration(Configuration):
    """
    A dummy :py:class:`betty.config.Configuration` implementation.
    """

    def __init__(self, value: str | None = None, /):
        super().__init__()
        self.value = value

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            assert_record(
                OptionalField(
                    "value",
                    assert_or(assert_none(), assert_str()),
                )
            )(dump)["value"]
        )

    @override
    def dump(self) -> Dump:
        if self.value is None:
            return {}
        return {
            "value": self.value,
        }


class DummyConfigurable(Configurable[DummyConfiguration]):
    """
    A dummy :py:class:`betty.config.Configurable` implementation.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[DummyConfiguration]:
        return DummyConfiguration
