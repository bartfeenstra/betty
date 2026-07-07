from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from betty.data import DataDefinition
from betty.datas.aggregate.record import (
    FieldDefinition,
    FieldPorter,
    RecordDefinition,
    resolve_field_definition,
)
from betty.datas.bool import BoolDefinition
from betty.datas.optional import OptionalDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Attr
from betty.localizables.plain import Plain
from betty.portable import Porter
from betty.portable.error import NotPortable
from betty.porters.data_definition_field import DataDefinitionFieldPorter
from betty.porters.fields import FieldsPorter


class TestFieldDefinition:
    def test_optional(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"))
        assert not sut.optional

    def test_optional__with_optional(self) -> None:
        sut = FieldDefinition(
            BoolDefinition(label="-"),
            optional=True,
        )
        assert sut.optional

    def test_optional__with_optional_definition(self) -> None:
        sut = FieldDefinition(
            OptionalDefinition(BoolDefinition(label="-")), optional=True
        )
        assert sut.optional

    def test_data(self) -> None:
        data = DataDefinition(label="-")
        sut = FieldDefinition(data)
        assert sut.data is data

    def test_label__with_label(self) -> None:
        label = Plain("-")
        sut = FieldDefinition(DataDefinition(label="-"), label=label)
        assert sut.label is label

    def test_description__without_description(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"))
        assert sut.description is None

    def test_description__with_description(self) -> None:
        description = Plain("-")
        sut = FieldDefinition(DataDefinition(label="-"), description=description)
        assert sut.description is description

    def test_porter__without_porter_without_data_porter(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"))
        with pytest.raises(NotPortable):
            assert sut.porter

    def test_porter__without_porter_with_data_porter(
        self, mocker: MockerFixture
    ) -> None:
        sut = FieldDefinition(
            DataDefinition(label="-", porter=mocker.MagicMock(spec=Porter))
        )
        assert isinstance(sut.porter, DataDefinitionFieldPorter)

    def test_porter__with_porter(self, mocker: MockerFixture) -> None:
        porter = mocker.MagicMock(spec=FieldPorter)
        sut = FieldDefinition(DataDefinition(label="-"), porter=porter)
        assert sut.porter is porter

    def test_try_porter__without_porter_without_data_porter(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"))
        assert sut.try_porter is None

    def test_try_porter__without_porter_with_data_porter(
        self, mocker: MockerFixture
    ) -> None:
        sut = FieldDefinition(
            DataDefinition(label="-", porter=mocker.MagicMock(spec=Porter))
        )
        assert isinstance(sut.porter, DataDefinitionFieldPorter)

    def test_try_porter__with_porter(self, mocker: MockerFixture) -> None:
        porter = mocker.MagicMock(spec=FieldPorter)
        sut = FieldDefinition(DataDefinition(label="-"), porter=porter)
        assert sut.try_porter is porter


@dataclass(frozen=True)
class RecordDefinitionTestRecord:
    my_first_element: str | None = None


@dataclass(frozen=True)
class RecordDefinitionTestFactoryRecord(RecordDefinitionTestRecord):
    pass


class TestRecordDefinition:
    def test_factory__without_factory(self) -> None:
        sut = RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
            cls=RecordDefinitionTestRecord, label="-"
        )
        assert sut.factory is RecordDefinitionTestRecord

    def test_factory__with_factory(self) -> None:
        def factory() -> RecordDefinitionTestRecord:
            return RecordDefinitionTestRecord()

        sut = RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
            cls=RecordDefinitionTestRecord, label="-", factory=factory
        )
        assert sut.factory is factory

    def test_porter__without_porter(self) -> None:
        sut = RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
            cls=RecordDefinitionTestRecord, label="-"
        )
        assert isinstance(sut.try_porter, FieldsPorter)

    def test_porter__with_porter(self) -> None:
        m_porter = Mock(spec=Porter)
        sut = RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
            cls=RecordDefinitionTestRecord, label="-", porter=m_porter
        )
        assert sut.try_porter is m_porter

    def test_fields(self) -> None:
        field = FieldDefinition(StrDefinition(label="-"))
        sut = RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
            cls=RecordDefinitionTestRecord,
            label="-",
            fields={Attr("my_first_element"): field},
        )
        assert dict(sut.fields) == {Attr("my_first_element"): field}


def test_resolve_field_definition__with_field_definition() -> None:
    field = FieldDefinition(DataDefinition(label="-"))
    assert resolve_field_definition(field) is field


def test_resolve_field_definition__with_resolvable_data_definition() -> None:
    data = DataDefinition(label="-")
    assert resolve_field_definition(data).data is data
