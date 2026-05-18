"""
Test utilities for :py:mod:`betty.data`.
"""

from typing import Any

import pytest

from betty.attrs.attr import AttrAttr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.importlib import fully_qualified_name
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.property import HasProperties


class DataTestBase[DataT: Data]:
    """
    A base class for testing :py:class:`betty.data.Data` subclasses.
    """

    sut_cls: type[DataT]
    """
    The system under test.
    """

    def test_data(self) -> None:
        """
        Tests :py:meth:`betty.data.Data.data` implementations.
        """
        self.sut_cls.data()

    def test_cls_docstring(self) -> None:
        """
        Test the class's docstring.
        """
        docstring = self.sut_cls.__doc__
        assert docstring, "Failed asserting that the class has a docstring"
        directive = f".. data:: {fully_qualified_name(self.sut_cls)}"
        assert directive in docstring, (
            f"Failed to find `{directive}` in the class's docstring"
        )

    def test_data__samples__should_provide_at_least_one(self) -> None:
        """
        Tests that the data definition provides at least one sample.
        """
        assert list(self.sut_cls.data().samples), (
            "Failed asserting that at least one sample is provided"
        )

    def test_data__porter__with_samples(self, subtests: pytest.Subtests) -> None:
        """
        Tests that the data definition can consistently dump and load its samples.
        """
        samples = list(self.sut_cls.data().samples)
        for sample in samples:
            with subtests.test(str(sample.label.localize(DEFAULT_LOCALIZER))):
                portable = self.sut_cls.data().porter.dump(sample.subject)
                loaded = self.sut_cls.data().porter.load(portable)
                dumped = self.sut_cls.data().porter.dump(loaded)
                assert self.sut_cls.data().porter.dump(loaded) == dumped, (
                    f'Failed asserting that repeatedly loading and dumping sample "{sample.label.localize(DEFAULT_LOCALIZER)}" keeps producing the same portable data'
                )
                for other_sample in samples:
                    if other_sample is sample:
                        continue
                    assert (
                        self.sut_cls.data().porter.dump(other_sample.subject) != dumped
                    ), (
                        f'Failed asserting that sample "{sample.label.localize(DEFAULT_LOCALIZER)}" instance is not equal to sample "{other_sample.label.localize(DEFAULT_LOCALIZER)}"'
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
    def test___eq____with_non_data_other(
        self, other: Any, subtests: pytest.Subtests
    ) -> None:
        """
        Tests :py:meth:`object.__eq__` implementations with values that do not subclass :py:class:`betty.data.Data`.
        """
        samples = list(self.sut_cls.data().samples)
        for sample in samples:
            with subtests.test(str(sample.label.localize(DEFAULT_LOCALIZER))):
                assert sample.subject != other

    def test___eq____with_samples(self, subtests: pytest.Subtests) -> None:
        """
        Tests :py:meth:`object.__eq__` implementations with the data definition's samples.
        """
        samples = list(self.sut_cls.data().samples)
        for sample in samples:
            with subtests.test(str(sample.label.localize(DEFAULT_LOCALIZER))):
                assert sample.subject == sample.subject, (
                    f'Failed asserting that sample "{sample.label.localize(DEFAULT_LOCALIZER)}" instance is equal to itself'
                )
                for other_sample in samples:
                    if other_sample is sample:
                        continue
                    assert sample.subject != other_sample.subject, (
                        f'Failed asserting that sample "{sample.label.localize(DEFAULT_LOCALIZER)}" instance is not equal to sample "{other_sample.label.localize(DEFAULT_LOCALIZER)}"'
                    )


@ObjectDefinition(label=Plain("Dummy data"))
class DummyData(Data, HasProperties):
    """
    A dummy :py:class:`betty.data.Data` implementation.
    """

    value = AttrAttr(StrDefinition(label="Value")).optional

    def __init__(self, /, value: str | None = None):
        super().__init__()
        self.value = value
