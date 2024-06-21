from pathlib import Path

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QColorDialog
from pytest_mock import MockerFixture

from betty.extension import CottonCandy
from betty.extension.cotton_candy import _ColorConfiguration
from betty.extension.cotton_candy.gui import (
    _CottonCandyGuiWidget,
    _ColorConfigurationWidget,
)
from betty.locale import Str, Localizable
from betty.model import Entity, UserFacingEntity
from betty.project import EntityReference
from betty.tests.conftest import BettyQtBot


class TestColorConfigurationWidget:
    async def test_configure(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        configured_hex_value = "#ffffff"
        color_configuration = _ColorConfiguration(hex_value="#000000")
        mocker.patch.object(
            QColorDialog,
            "getColor",
            mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)),
        )
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        sut = _ColorConfigurationWidget(
            betty_qtbot.app, color_configuration, configured_hex_value
        )
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        sut._configure.click()
        assert configured_hex_value == color_configuration.hex

    async def test_reset(self, betty_qtbot: BettyQtBot) -> None:
        default_hex_value = "#ffffff"
        color_configuration = _ColorConfiguration(hex_value="#000000")
        sut = _ColorConfigurationWidget(
            betty_qtbot.app, color_configuration, default_hex_value
        )
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        sut._reset.click()
        assert default_hex_value == color_configuration.hex


class CottonCandyGuiWidgetTestEntity(UserFacingEntity, Entity):
    @classmethod
    def entity_type_label(cls) -> Localizable:
        return Str.plain(cls.__name__)

    @classmethod
    def entity_type_label_plural(cls) -> Localizable:
        return Str.plain(cls.__name__)


class TestCottonCandyGuiWidget:
    async def test_add_featured_entities(self, betty_qtbot: BettyQtBot) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        entity_id = "123"
        betty_qtbot.mouse_click(
            sut._featured_entities_entity_references_collector._add_entity_reference_button
        )
        # @todo Find out an elegant way to test changing the entity type.
        sut._featured_entities_entity_references_collector._entity_reference_collectors[
            0
        ]._entity_id.setText(entity_id)
        assert (
            betty_qtbot.app.extensions[CottonCandy]
            .configuration.featured_entities[0]
            .entity_id
            == entity_id
        )

    async def test_change_featured_entities(self, betty_qtbot: BettyQtBot) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        entity_reference_1 = EntityReference(CottonCandyGuiWidgetTestEntity, "123")
        entity_reference_2 = EntityReference(CottonCandyGuiWidgetTestEntity, "456")
        entity_reference_3 = EntityReference(CottonCandyGuiWidgetTestEntity, "789")
        betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities.append(
            entity_reference_1,  # type: ignore[arg-type]
        )
        betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities.append(
            entity_reference_2,  # type: ignore[arg-type]
        )
        betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities.append(
            entity_reference_3,  # type: ignore[arg-type]
        )
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        entity_id = "123"
        # @todo Find out an elegant way to test changing the entity type.
        sut._featured_entities_entity_references_collector._entity_reference_collectors[
            1
        ]._entity_id.setText(entity_id)
        assert (
            betty_qtbot.app.extensions[CottonCandy]
            .configuration.featured_entities[1]
            .entity_id
            == entity_id
        )

    async def test_remove_featured_entities(self, betty_qtbot: BettyQtBot) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        entity_reference_1 = EntityReference[CottonCandyGuiWidgetTestEntity](
            CottonCandyGuiWidgetTestEntity, "123"
        )
        entity_reference_2 = EntityReference[CottonCandyGuiWidgetTestEntity](
            CottonCandyGuiWidgetTestEntity, "456"
        )
        entity_reference_3 = EntityReference[CottonCandyGuiWidgetTestEntity](
            CottonCandyGuiWidgetTestEntity, "789"
        )
        betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities.append(
            entity_reference_1,  # type: ignore[arg-type]
        )
        betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities.append(
            entity_reference_2,  # type: ignore[arg-type]
        )
        betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities.append(
            entity_reference_3,  # type: ignore[arg-type]
        )
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.mouse_click(
            sut._featured_entities_entity_references_collector._entity_reference_remove_buttons[
                1
            ]
        )
        assert (
            entity_reference_1
            in betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities
        )
        assert (
            entity_reference_2
            not in betty_qtbot.app.extensions[
                CottonCandy
            ].configuration.featured_entities
        )
        assert (
            entity_reference_3
            in betty_qtbot.app.extensions[CottonCandy].configuration.featured_entities
        )

    async def test_change_primary_inactive_color(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        configured_hex_value = "#ffffff"
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        mocker.patch.object(
            QColorDialog,
            "getColor",
            mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)),
        )
        sut._color_configurations_widget._color_configurations[0]._configure.click()
        assert (
            configured_hex_value
            == betty_qtbot.app.extensions[
                CottonCandy
            ].configuration.primary_inactive_color.hex
        )

    async def test_change_primary_active_color(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        configured_hex_value = "#ffffff"
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        mocker.patch.object(
            QColorDialog,
            "getColor",
            mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)),
        )
        sut._color_configurations_widget._color_configurations[1]._configure.click()
        assert (
            configured_hex_value
            == betty_qtbot.app.extensions[
                CottonCandy
            ].configuration.primary_active_color.hex
        )

    async def test_change_link_inactive_color(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        configured_hex_value = "#ffffff"
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        mocker.patch.object(
            QColorDialog,
            "getColor",
            mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)),
        )
        sut._color_configurations_widget._color_configurations[2]._configure.click()
        assert (
            configured_hex_value
            == betty_qtbot.app.extensions[
                CottonCandy
            ].configuration.link_inactive_color.hex
        )

    async def test_change_link_active_color(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        configured_hex_value = "#ffffff"
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        mocker.patch.object(
            QColorDialog,
            "getColor",
            mocker.MagicMock(return_value=QColor.fromString(configured_hex_value)),
        )
        sut._color_configurations_widget._color_configurations[3]._configure.click()
        assert (
            configured_hex_value
            == betty_qtbot.app.extensions[
                CottonCandy
            ].configuration.link_active_color.hex
        )

    async def test_set_logo(self, betty_qtbot: BettyQtBot, tmp_path: Path) -> None:
        logo = tmp_path / "logo.png"
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        sut._logo.setText(str(logo))
        assert betty_qtbot.app.extensions[CottonCandy].configuration.logo == logo

    async def test_unset_logo(self, betty_qtbot: BettyQtBot, tmp_path: Path) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(CottonCandy)
        betty_qtbot.app.extensions[CottonCandy].configuration.logo = (
            tmp_path / "logo.png"
        )
        sut = _CottonCandyGuiWidget(betty_qtbot.app)
        sut._logo.setText("")
        assert betty_qtbot.app.extensions[CottonCandy].configuration.logo is None
