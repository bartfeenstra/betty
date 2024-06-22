"""
Provide the GRaphical User Interface for the Wikipedia extension.
"""

from typing import Any

from PyQt6.QtWidgets import (
    QFormLayout,
    QWidget,
    QCheckBox,
)

from betty.app import App
from betty.extension.wikipedia.config import WikipediaConfiguration
from betty.gui.text import Caption
from betty.project import ProjectAwareMixin


class _WikipediaGuiWidget(ProjectAwareMixin, QWidget):
    def __init__(
        self, app: App, configuration: WikipediaConfiguration, *args: Any, **kwargs: Any
    ):
        super().__init__(app.project, *args, **kwargs)
        self._app = app
        self._configuration = configuration
        layout = QFormLayout()

        self.setLayout(layout)

        def _update_configuration_populate_images(checked: bool) -> None:
            self._configuration.populate_images = checked

        self._populate_images = QCheckBox(self._app.localizer._("Populate images"))
        self._populate_images.setChecked(self._configuration.populate_images)
        self._populate_images.toggled.connect(_update_configuration_populate_images)
        layout.addRow(self._populate_images)
        self._populate_images_caption = Caption(
            self._app.localizer._(
                "Download images from the Wikipedia links in your ancestry"
            )
        )
        layout.addRow(self._populate_images_caption)
