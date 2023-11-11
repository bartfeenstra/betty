from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from betty.app import App
from betty.extension import CottonCandy
from betty.extension.cotton_candy import _ColorConfiguration
from betty.extension.cotton_candy.gui import _CottonCandyGuiWidget, _ColorConfigurationWidget
from betty.locale import Localizer
from betty.model import Entity, UserFacingEntity
from betty.project import EntityReference


class TestColorConfigurationWidget:
    async def test_configure(self, qtbot: QtBot, mocker: MockerFixture) -> None:
        configured_hex_value = '#ffffff'
        color_configuration = _ColorConfiguration(hex_value='#000000')
        mocker.patch.object(QColorDialog, 'getColor', mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)))
        async with App() as app:
            sut = _ColorConfigurationWidget(app, color_configuration, configured_hex_value)
            sut._configure.click()
        assert configured_hex_value == color_configuration.hex

    async def test_reset(self, qtbot: QtBot) -> None:
        default_hex_value = '#ffffff'
        color_configuration = _ColorConfiguration(hex_value='#000000')
        async with App() as app:
            sut = _ColorConfigurationWidget(app, color_configuration, default_hex_value)
            qtbot.addWidget(sut)
            sut.show()
            sut._reset.click()
        assert default_hex_value == color_configuration.hex


class CottonCandyGuiWidgetTestEntity(UserFacingEntity, Entity):
    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        return cls.__name__

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        return cls.__name__


class TestCottonCandyGuiWidget:
    async def test_add_featured_entities(self, qtbot: QtBot) -> None:
        async with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            sut = _CottonCandyGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            entity_id = '123'
            qtbot.mouseClick(sut._featured_entities_entity_references_collector._add_entity_reference_button, Qt.MouseButton.LeftButton)
            # @todo Find out an elegant way to test changing the entity type.
            sut._featured_entities_entity_references_collector._entity_reference_collectors[0]._entity_id.setText(entity_id)
            assert app.extensions[CottonCandy].configuration.featured_entities[0].entity_id == entity_id

    async def test_change_featured_entities(self, qtbot: QtBot) -> None:
        async with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            entity_reference_1 = EntityReference(CottonCandyGuiWidgetTestEntity, '123')
            entity_reference_2 = EntityReference(CottonCandyGuiWidgetTestEntity, '456')
            entity_reference_3 = EntityReference(CottonCandyGuiWidgetTestEntity, '789')
            app.extensions[CottonCandy].configuration.featured_entities.append(
                entity_reference_1,  # type: ignore[arg-type]
            )
            app.extensions[CottonCandy].configuration.featured_entities.append(
                entity_reference_2,  # type: ignore[arg-type]
            )
            app.extensions[CottonCandy].configuration.featured_entities.append(
                entity_reference_3,  # type: ignore[arg-type]
            )
            sut = _CottonCandyGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            entity_id = '123'
            # @todo Find out an elegant way to test changing the entity type.
            sut._featured_entities_entity_references_collector._entity_reference_collectors[1]._entity_id.setText(entity_id)
            assert app.extensions[CottonCandy].configuration.featured_entities[1].entity_id == entity_id

    async def test_remove_featured_entities(self, qtbot: QtBot) -> None:
        async with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            entity_reference_1 = EntityReference[CottonCandyGuiWidgetTestEntity](CottonCandyGuiWidgetTestEntity, '123')
            entity_reference_2 = EntityReference[CottonCandyGuiWidgetTestEntity](CottonCandyGuiWidgetTestEntity, '456')
            entity_reference_3 = EntityReference[CottonCandyGuiWidgetTestEntity](CottonCandyGuiWidgetTestEntity, '789')
            app.extensions[CottonCandy].configuration.featured_entities.append(
                entity_reference_1,  # type: ignore[arg-type]
            )
            app.extensions[CottonCandy].configuration.featured_entities.append(
                entity_reference_2,  # type: ignore[arg-type]
            )
            app.extensions[CottonCandy].configuration.featured_entities.append(
                entity_reference_3,  # type: ignore[arg-type]
            )
            sut = _CottonCandyGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            qtbot.mouseClick(sut._featured_entities_entity_references_collector._entity_reference_remove_buttons[1], Qt.MouseButton.LeftButton)
            assert entity_reference_1 in app.extensions[CottonCandy].configuration.featured_entities
            assert entity_reference_2 not in app.extensions[CottonCandy].configuration.featured_entities
            assert entity_reference_3 in app.extensions[CottonCandy].configuration.featured_entities

    async def test_change_primary_inactive_color(self, qtbot: QtBot, mocker: MockerFixture) -> None:
        configured_hex_value = '#ffffff'
        async with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            sut = _CottonCandyGuiWidget(app)
            mocker.patch.object(QColorDialog, 'getColor', mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)))
            sut._color_configurations_widget._color_configurations[0]._configure.click()
        assert configured_hex_value == app.extensions[CottonCandy].configuration.primary_inactive_color.hex

    async def test_change_primary_active_color(self, qtbot: QtBot, mocker: MockerFixture) -> None:
        configured_hex_value = '#ffffff'
        async with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            sut = _CottonCandyGuiWidget(app)
            mocker.patch.object(QColorDialog, 'getColor', mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)))
            sut._color_configurations_widget._color_configurations[1]._configure.click()
        assert configured_hex_value == app.extensions[CottonCandy].configuration.primary_active_color.hex

    async def test_change_link_inactive_color(self, qtbot: QtBot, mocker: MockerFixture) -> None:
        configured_hex_value = '#ffffff'
        async with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            sut = _CottonCandyGuiWidget(app)
            mocker.patch.object(QColorDialog, 'getColor', mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)))
            sut._color_configurations_widget._color_configurations[2]._configure.click()
        assert configured_hex_value == app.extensions[CottonCandy].configuration.link_inactive_color.hex

    async def test_change_link_active_color(self, qtbot: QtBot, mocker: MockerFixture) -> None:
        configured_hex_value = '#ffffff'
        async with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            sut = _CottonCandyGuiWidget(app)
            mocker.patch.object(QColorDialog, 'getColor', mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)))
            sut._color_configurations_widget._color_configurations[3]._configure.click()
        assert configured_hex_value == app.extensions[CottonCandy].configuration.link_active_color.hex
