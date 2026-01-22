import pytest

from betty.data import DataDefinition
from betty.data.aggregate.record import FieldDefinition, RecordDefinition
from betty.data.indicator.selector import Attr, Key
from betty.data.str import StrDefinition
from betty.exception import HumanFacingException
from betty.locale.localizable.plain import Plain
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestFieldDefinition:
    def test_selector(self) -> None:
        selector = Key("my_first_key")
        sut = FieldDefinition(selector, DataDefinition(label=DUMMY_LOCALIZABLE))
        assert sut.selector is selector

    def test_data(self) -> None:
        data = DataDefinition(label=DUMMY_LOCALIZABLE)
        sut = FieldDefinition(Key("_"), data)
        assert sut.data is data

    def test_label__with_label(self) -> None:
        label = Plain("-")
        sut = FieldDefinition(
            Key("_"), DataDefinition(label=DUMMY_LOCALIZABLE), label=label
        )
        assert sut.label is label

    def test_description__without_description(self) -> None:
        sut = FieldDefinition(Key("_"), DataDefinition(label=DUMMY_LOCALIZABLE))
        assert sut.description is None

    def test_description__with_description(self) -> None:
        description = Plain("-")
        sut = FieldDefinition(
            Key("_"), DataDefinition(label=DUMMY_LOCALIZABLE), description=description
        )
        assert sut.description is description

    def test_required(self) -> None:
        sut = FieldDefinition(
            Key("_"), DataDefinition(label=DUMMY_LOCALIZABLE), required=False
        )
        assert not sut.required

    def test_empty__without_callback(self) -> None:
        sut = FieldDefinition(Key("_"), DataDefinition(label=DUMMY_LOCALIZABLE))
        assert not sut.empty(object())

    def test_empty__with_field_callback(self) -> None:
        sut = FieldDefinition(
            Key("_"), DataDefinition(label=DUMMY_LOCALIZABLE), empty=lambda _: True
        )
        assert sut.empty(object())

    def test_empty__with_data_callback(self) -> None:
        sut = FieldDefinition(
            Key("_"), DataDefinition(label=DUMMY_LOCALIZABLE, empty=lambda _: True)
        )
        assert sut.empty(object())


class RecordDefinitionTestRecord:
    def __init__(self, my_first_element: str | None = None):
        self.my_first_element = my_first_element


class RecordDefinitionTestFactoryRecord(RecordDefinitionTestRecord):
    pass


class TestRecordDefinition:
    def test_fields(self) -> None:
        element = FieldDefinition(
            Attr("my_first_element"), StrDefinition(label=DUMMY_LOCALIZABLE)
        )
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[element],
        )
        assert list(sut.fields) == [element]

    def test_elements(self) -> None:
        selector = Attr("my_first_element")
        element = StrDefinition(label=DUMMY_LOCALIZABLE)
        field = FieldDefinition(selector, element)
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[field],
        )
        assert list(sut.elements(RecordDefinitionTestRecord())) == [(selector, element)]

    def test_load__required_with_value(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                )
            ],
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert data.my_first_element == value

    def test_load__required_without_value(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                )
            ],
        )
        with pytest.raises(HumanFacingException):
            sut.load({})

    def test_load__optional_with_value(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name),
                    StrDefinition(label=DUMMY_LOCALIZABLE),
                    required=False,
                )
            ],
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert data.my_first_element == value

    def test_load__optional_without_value(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name),
                    StrDefinition(label=DUMMY_LOCALIZABLE),
                    required=False,
                )
            ],
        )
        sut.load({})

    def test_load__with_factory(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                )
            ],
            factory=RecordDefinitionTestFactoryRecord,
        )
        value = "Hello, world!"
        data = sut.load({field_name: value})
        assert isinstance(data, RecordDefinitionTestFactoryRecord)
        assert data.my_first_element == value

    def test_dump(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                )
            ],
        )
        value = "Hello, world!"
        data = RecordDefinitionTestRecord(value)
        assert sut.dump(data) == {field_name: value}

    def test_load_key(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                )
            ],
        )
        value = "Hello, world!"
        data = sut.load_key({}, Attr(field_name), value)
        assert data.my_first_element == value

    def test_dump_key(self) -> None:
        field_name = "my_first_element"
        sut = RecordDefinition[RecordDefinitionTestRecord, Attr](
            cls=RecordDefinitionTestRecord,
            label=DUMMY_LOCALIZABLE,
            fields=[
                FieldDefinition(
                    Attr(field_name), StrDefinition(label=DUMMY_LOCALIZABLE)
                )
            ],
        )
        value = "Hello, world!"
        data = RecordDefinitionTestRecord(value)
        assert sut.dump_key(data, Attr(field_name)) == (value, {})
