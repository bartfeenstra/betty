from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from betty.app import App
from betty.cotton_candy import CottonCandy
from betty.gui.model import EntityReferencesCollector

if TYPE_CHECKING:
    from betty.builtins import _


class _CottonCandyGuiWidget(QWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._featured_entities_label = QLabel()
        self._layout.addWidget(self._featured_entities_label)
        self._featured_entities_entity_references_collector = EntityReferencesCollector(
            self._app,
            self._app.extensions[CottonCandy].configuration.featured_entities,
            lambda: _('Featured entities'),
            lambda: _("These entities are featured on your site's front page."),
        )
        self._layout.addWidget(self._featured_entities_entity_references_collector)
