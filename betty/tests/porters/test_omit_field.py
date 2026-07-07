from collections.abc import Sized

import pytest
from pytest_mock import MockerFixture

from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.nothing import Nothing
from betty.portable import PortableData, Porter
from betty.porters.omit_field import OmitFieldPorter


class TestOmitFieldPorter:
    def test_dump__without_omit(self, mocker: MockerFixture) -> None:
        dumped: PortableData = {
            "hello": "World!",
        }
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.dump.return_value = dumped
        sut = OmitFieldPorter(
            FieldDefinition(DataDefinition(label="-", porter=m_porter)), lambda _: False
        )
        data = object()
        assert sut.dump(object(), data) == dumped
        m_porter.dump.assert_called_once_with(data)

    def test_dump__with_omit(self) -> None:
        sut = OmitFieldPorter(
            FieldDefinition(DataDefinition(label="-")), lambda _: True
        )
        assert sut.dump(object(), object()) is Nothing

    def test_load(self, mocker: MockerFixture) -> None:
        loaded = object()
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.load.return_value = loaded
        sut = OmitFieldPorter(
            FieldDefinition(DataDefinition(label="-", porter=m_porter)), lambda _: False
        )
        dumped: PortableData = {
            "hello": "World!",
        }
        assert sut.load(dumped) is loaded
        m_porter.load.assert_called_once_with(dumped)

    def test_new__dump_without_omit(self, mocker: MockerFixture) -> None:
        dumped: PortableData = {
            "hello": "World!",
        }
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.dump.return_value = dumped
        sut = OmitFieldPorter.new(lambda _: False)(
            FieldDefinition(DataDefinition(label="-", porter=m_porter))
        )
        data = object()
        assert sut.dump(object(), data) == dumped
        m_porter.dump.assert_called_once_with(data)

    def test_new__dump_with_omit(self) -> None:
        sut = OmitFieldPorter.new(lambda _: True)(
            FieldDefinition(DataDefinition(label="-"))
        )
        assert sut.dump(object(), object()) is Nothing

    @pytest.mark.parametrize(
        "data",
        [
            " ",
            [""],
            ("",),
            {""},
            {"": ""},
        ],
    )
    def test_new_is_empty__dump_without_omit(
        self, data: Sized, mocker: MockerFixture
    ) -> None:
        dumped: PortableData = {
            "hello": "World!",
        }
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.dump.return_value = dumped
        sut = OmitFieldPorter.new_is_empty(
            FieldDefinition(DataDefinition(label="-", porter=m_porter))
        )
        assert sut.dump(object(), data) == dumped
        m_porter.dump.assert_called_once_with(data)

    @pytest.mark.parametrize(
        "data",
        [
            "",
            [],
            (),
            set(),
            {},
        ],
    )
    def test_new_is_empty__dump_with_omit(self, data: Sized) -> None:
        sut = OmitFieldPorter.new_is_empty(FieldDefinition(DataDefinition(label="-")))
        assert sut.dump(object(), data) is Nothing

    def test_new_is_none__dump_without_omit(self, mocker: MockerFixture) -> None:
        dumped: PortableData = {
            "hello": "World!",
        }
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.dump.return_value = dumped
        sut = OmitFieldPorter.new_is_none(
            FieldDefinition(DataDefinition(label="-", porter=m_porter))
        )
        data = object()
        assert sut.dump(object(), data) == dumped
        m_porter.dump.assert_called_once_with(data)

    def test_new_is_none__dump_with_omit(self) -> None:
        sut = OmitFieldPorter.new_is_none(FieldDefinition(DataDefinition(label="-")))
        assert sut.dump(object(), None) is Nothing
