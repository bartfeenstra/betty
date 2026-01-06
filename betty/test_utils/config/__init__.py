"""
Test utilities for :py:mod:`betty.config`.
"""

from inspect import isabstract
from typing import Generic, Self

import pytest
from typing_extensions import TypeVar, override

from betty.assertion import (
    OptionalField,
    assert_none,
    assert_or,
    assert_record,
    assert_str,
)
from betty.config import Configurable, Configuration
from betty.importlib import fully_qualified_name
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.serde.dump import Dump

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationTestBase(Generic[_ConfigurationT]):
    """
    A base class for testing :py:class:`betty.config.Configuration` implementations.
    """

    sut_cls: type[_ConfigurationT]

    def test_docstring(self) -> None:
        """
        Test the configuration class's docstring.
        """
        if isabstract(self.sut_cls):
            return
        docstring = self.sut_cls.__doc__
        assert docstring, (
            f"{fully_qualified_name(self.sut_cls)}.samples() does not have a docstring."
        )
        directive = f".. configuration:: {fully_qualified_name(self.sut_cls)}"
        assert directive in docstring, (
            f"Failed to find `{directive}` in the docstring for {fully_qualified_name(self.sut_cls)}."
        )

    def test_samples(self) -> None:
        """
        Tests :py:meth:`betty.config.Configuration.samples` implementations.
        """
        if isabstract(self.sut_cls):
            return
        assert len(list(self.sut_cls.samples())), (
            f"{fully_qualified_name(self.sut_cls)}.samples() does not return any samples."
        )

    def test___eq__(self, subtests: pytest.Subtests) -> None:
        """
        Tests :py:meth:`object.__eq__` implementations.
        """
        for sample in self.sut_cls.samples():
            with subtests.test(str(sample.label.localize(DEFAULT_LOCALIZER))):
                assert sample == sample
                for other_sample in self.sut_cls.samples():
                    assert sample != other_sample


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
