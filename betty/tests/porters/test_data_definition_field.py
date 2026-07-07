from typing import TYPE_CHECKING

import pytest
from pytest_mock import MockerFixture

from betty.data import DataDefinition
from betty.portable import Porter
from betty.portable.error import NotPortable
from betty.porters.data_definition_field import DataDefinitionFieldPorter

if TYPE_CHECKING:
    from betty.portable import PortableData


class TestDataDefinitionFieldPorter:
    def test_dump__without_porter(self) -> None:
        sut = DataDefinitionFieldPorter(DataDefinition(label="-"))
        with pytest.raises(NotPortable):
            sut.dump(object(), object())

    def test_dump__with_porter(self, mocker: MockerFixture) -> None:
        dumped: PortableData = {"hello": "world"}
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.dump.return_value = dumped
        sut = DataDefinitionFieldPorter(DataDefinition(porter=m_porter, label="-"))
        data = object()
        assert sut.dump(object(), data) == dumped
        m_porter.dump.assert_called_once_with(data)

    def test_load__without_porter(self) -> None:
        sut = DataDefinitionFieldPorter(DataDefinition(label="-"))
        with pytest.raises(NotPortable):
            sut.load(None)

    def test_load__with_porter(self, mocker: MockerFixture) -> None:
        data = object()
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.load.return_value = data
        sut = DataDefinitionFieldPorter(DataDefinition(porter=m_porter, label="-"))
        dumped: PortableData = {"hello": "world"}
        assert sut.load(dumped) is data
        m_porter.load.assert_called_once_with(dumped)
