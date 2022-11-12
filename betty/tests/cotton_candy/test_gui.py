from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from betty.app import App
from betty.cotton_candy import CottonCandy
from betty.cotton_candy.gui import _CottonCandyGuiWidget
from betty.model import Entity
from betty.project import EntityReference


class TestCottonCandyGuiWidget:
    def test_add_featured_entities(self, qtbot: QtBot) -> None:
        with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            sut = _CottonCandyGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            entity_id = '123'
            qtbot.mouseClick(sut._featured_entities_entity_references_collector._add_entity_reference_button, Qt.MouseButton.LeftButton)
            # @todo Find out an elegant way to test changing the entity type.
            sut._featured_entities_entity_references_collector._entity_reference_collectors[0]._entity_id.setText(entity_id)
            assert app.extensions[CottonCandy].configuration.featured_entities[0].entity_id == entity_id

    def test_change_featured_entities(self, qtbot: QtBot) -> None:
        with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            entity_reference_1 = EntityReference(Entity, '123')
            entity_reference_2 = EntityReference(Entity, '456')
            entity_reference_3 = EntityReference(Entity, '789')
            app.extensions[CottonCandy].configuration.featured_entities.append(entity_reference_1)
            app.extensions[CottonCandy].configuration.featured_entities.append(entity_reference_2)
            app.extensions[CottonCandy].configuration.featured_entities.append(entity_reference_3)
            sut = _CottonCandyGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            entity_id = '123'
            # @todo Find out an elegant way to test changing the entity type.
            sut._featured_entities_entity_references_collector._entity_reference_collectors[1]._entity_id.setText(entity_id)
            assert app.extensions[CottonCandy].configuration.featured_entities[1].entity_id == entity_id

    def test_remove_featured_entities(self, qtbot: QtBot) -> None:
        with App() as app:
            app.project.configuration.extensions.enable(CottonCandy)
            entity_reference_1 = EntityReference(Entity, '123')
            entity_reference_2 = EntityReference(Entity, '456')
            entity_reference_3 = EntityReference(Entity, '789')
            app.extensions[CottonCandy].configuration.featured_entities.append(entity_reference_1)
            app.extensions[CottonCandy].configuration.featured_entities.append(entity_reference_2)
            app.extensions[CottonCandy].configuration.featured_entities.append(entity_reference_3)
            sut = _CottonCandyGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            qtbot.mouseClick(sut._featured_entities_entity_references_collector._entity_reference_remove_buttons[1], Qt.MouseButton.LeftButton)
            assert entity_reference_1 in app.extensions[CottonCandy].configuration.featured_entities
            assert entity_reference_2 not in app.extensions[CottonCandy].configuration.featured_entities
            assert entity_reference_3 in app.extensions[CottonCandy].configuration.featured_entities
