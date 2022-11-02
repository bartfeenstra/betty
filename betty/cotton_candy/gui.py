from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from betty.app import App
from betty.cotton_candy import CottonCandy
from betty.gui.model import EntityReferenceCollector, EntityReferencesCollector
from betty.gui.text import Caption

if TYPE_CHECKING:
    from betty.builtins import _


class _CottonCandyGuiWidget(QWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._background_image_label = QLabel()
        self._layout.addWidget(self._background_image_label)
        self._background_image_entity_reference_collector = EntityReferenceCollector(
            self._app,
            self._app.extensions[CottonCandy].configuration.background_image,
            lambda: _('Background image'),
            lambda: _('The ID of the file entity whose (image) file to use for page backgrounds if a page does not provide any image media itself.'),
        )
        self._layout.addWidget(self._background_image_entity_reference_collector)
        self._background_image_caption = Caption()
        self._layout.addWidget(self._background_image_caption)

        self._featured_entities_label = QLabel()
        self._layout.addWidget(self._featured_entities_label)
        self._featured_entities_entity_references_collector = EntityReferencesCollector(
            self._app,
            self._app.extensions[CottonCandy].configuration.featured_entities,
            lambda: _('Featured entities'),
            lambda: _("These entities are featured on your site's front page."),
        )
        self._layout.addWidget(self._featured_entities_entity_references_collector)
