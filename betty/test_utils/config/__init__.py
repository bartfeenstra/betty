"""
Test utilities for :py:mod:`betty.config`.
"""

from inspect import isabstract
from typing import Any, Generic, Self

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
from betty.data import Data
from betty.data.aggregate.record.object import ObjectDefinition
from betty.importlib import fully_qualified_name
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.portable import PortableData

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
            f"{fully_qualified_name(self.sut_cls)} does not have a docstring."
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

    @pytest.mark.parametrize(
        "other",
        [
            object,
            object(),
            True,
            False,
            None,
            123,
            "abc",
            [],
            {},
        ],
    )
    def test___eq____with_unsupported_other(
        self, other: Any, subtests: pytest.Subtests
    ) -> None:
        """
        Tests :py:meth:`object.__eq__` implementations.
        """
        samples = list(self.sut_cls.samples())
        for sample in samples:
            with subtests.test(str(sample.label.localize(DEFAULT_LOCALIZER))):
                assert sample.data != other

    def test___eq____with_samples(self, subtests: pytest.Subtests) -> None:
        """
        Tests :py:meth:`object.__eq__` implementations.
        """
        samples = list(self.sut_cls.samples())
        for sample in samples:
            with subtests.test(str(sample.label.localize(DEFAULT_LOCALIZER))):
                assert sample.data == sample.data, (
                    f'Failed asserting that {fully_qualified_name(self.sut_cls)} sample "{sample.label.localize(DEFAULT_LOCALIZER)}" instance is equal to itself.'
                )
                for other_sample in samples:
                    if other_sample is sample:
                        continue
                    assert sample.data != other_sample.data, (
                        f'Failed asserting that {fully_qualified_name(self.sut_cls)} sample "{sample.label.localize(DEFAULT_LOCALIZER)}" instance is not equal to sample "{sample.label.localize(DEFAULT_LOCALIZER)}".'
                    )

    def test_dump__with_samples(self, subtests: pytest.Subtests) -> None:
        """
        Tests :py:meth:`object.__eq__` implementations.
        """
        samples = list(self.sut_cls.samples())
        for sample in samples:
            with subtests.test(str(sample.label.localize(DEFAULT_LOCALIZER))):
                portable = sample.data.dump()
                assert portable == self.sut_cls.load(portable).dump(), (
                    f'Failed asserting that {fully_qualified_name(self.sut_cls)}.load() and {fully_qualified_name(self.sut_cls)}.dump() do not change the data for sample "{sample.label.localize(DEFAULT_LOCALIZER)}".'
                )
                for other_sample in samples:
                    if other_sample is sample:
                        continue
                    assert portable != other_sample.data.dump()


@ObjectDefinition(
    label=Plain("Dummy configuration"),
    fields=[],
)
class DummyConfiguration(Configuration, Data):
    """
    A dummy :py:class:`betty.config.Configuration` implementation.
    """

    def __init__(self, value: str | None = None, /):
        super().__init__()
        self.value = value

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(
            assert_record(
                OptionalField(
                    "value",
                    assert_or(assert_none, assert_str()),
                )
            )(portable)["value"]
        )

    @override
    def dump(self) -> PortableData:
        if self.value is None:
            return {}
        return {
            "value": self.value,
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.value == other.value


class DummyConfigurable(Configurable[DummyConfiguration]):
    """
    A dummy :py:class:`betty.config.Configurable` implementation.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[DummyConfiguration]:
        return DummyConfiguration
