from dataclasses import dataclass
from unittest.mock import Mock

from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition, RecordDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.optional import OptionalDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Attr
from betty.localizables.plain import Plain
from betty.portable import Porter
from betty.porters.fields import FieldsPorter


class TestFieldDefinition:
    def test_omit_load(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"))
        assert not sut.omit_load

    def test_omit_load__with_omit_load(self) -> None:
        sut = FieldDefinition(
            BoolDefinition(label="-"),
            omit_load=True,
        )
        assert sut.omit_load

    def test_omit_load__with_optional_definition(self) -> None:
        sut = FieldDefinition(
            OptionalDefinition(BoolDefinition(label="-")), omit_load=True
        )
        assert sut.omit_load

    def test_omit_dump__with_callable_false(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"), omit_dump=lambda _: False)
        assert not sut.omit_dump(object(), True)

    def test_omit_dump__with_callable_true(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"), omit_dump=lambda _: True)
        assert sut.omit_dump(object(), True)

    def test_omit_dump__with_none(self) -> None:
        sut = FieldDefinition(BoolDefinition(label="-"), omit_dump=None)
        assert not sut.omit_dump(object(), True)

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

    def test_omit__without_callback(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"))
        assert not sut.omit_dump(object(), object())

    def test_omit__with_callback(self) -> None:
        sut = FieldDefinition(DataDefinition(label="-"), omit_dump=lambda _: True)
        assert sut.omit_dump(object(), object())


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
        assert isinstance(sut.porter, FieldsPorter)

    def test_porter__with_porter(self) -> None:
        m_porter = Mock(spec=Porter)
        sut = RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
            cls=RecordDefinitionTestRecord, label="-", porter=m_porter
        )
        assert sut.porter is m_porter

    def test_fields(self) -> None:
        field = FieldDefinition(StrDefinition(label="-"))
        sut = RecordDefinition[RecordDefinitionTestRecord, Porter, Attr](
            cls=RecordDefinitionTestRecord,
            label="-",
            fields={Attr("my_first_element"): field},
        )
        assert dict(sut.fields) == {Attr("my_first_element"): field}
