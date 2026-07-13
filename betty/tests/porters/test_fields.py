import pytest

from betty.datas.aggregate.record import FieldDefinition, RecordDefinition
from betty.datas.str import StrDefinition
from betty.exception import HumanFacingException
from betty.indicator.selector import Attr
from betty.portable import Porter
from betty.porters.fields import FieldsPorter
from betty.tests.datas.aggregate.test_record import (
    RecordDefinitionTestFactoryRecord,
    RecordDefinitionTestRecord,
)


class TestFieldsPorter:
    def test_load__with_value(self) -> None:
        field_name = "my_first_element"
        sut = FieldsPorter(
            RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert data.my_first_element == value

    def test_load__without_value(self) -> None:
        field_name = "my_first_element"
        sut = FieldsPorter(
            RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        with pytest.raises(HumanFacingException):
            sut.load({})

    def test_load__with_factory(self) -> None:
        field_name = "my_first_element"
        sut = FieldsPorter(
            RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
                factory=RecordDefinitionTestFactoryRecord,
            )
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert isinstance(data, RecordDefinitionTestFactoryRecord)
        assert data.my_first_element == value

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = FieldsPorter(
            RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
                cls=RecordDefinitionTestRecord,
                label="-",
                fields={Attr(field_name): FieldDefinition(StrDefinition(label="-"))},
            )
        )
        value = "Hello, world!"
        data = RecordDefinitionTestRecord(value)
        assert sut.dump(data) == {field_name: value}
