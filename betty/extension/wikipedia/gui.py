"""
Provide the GRaphical User Interface for the Wikipedia extension.
"""

from typing import Any

from PyQt6.QtWidgets import (
    QFormLayout,
    QWidget,
    QCheckBox,
)
from typing_extensions import override

from betty.app import App
from betty.extension.wikipedia.config import WikipediaConfiguration
from betty.gui.locale import LocalizedObject
from betty.gui.text import Caption
from betty.project import ProjectAwareMixin


class _WikipediaGuiWidget(LocalizedObject, ProjectAwareMixin, QWidget):
    def __init__(
        self, app: App, configuration: WikipediaConfiguration, *args: Any, **kwargs: Any
    ):
        super().__init__(app, app.project, *args, **kwargs)
        self._app = app
        self._configuration = configuration
        layout = QFormLayout()

        self.setLayout(layout)

        def _update_configuration_populate_images(checked: bool) -> None:
            self._configuration.populate_images = checked

        self._populate_images = QCheckBox()
        self._populate_images.setChecked(self._configuration.populate_images)
        self._populate_images.toggled.connect(_update_configuration_populate_images)
        layout.addRow(self._populate_images)
        self._populate_images_caption = Caption()
        layout.addRow(self._populate_images_caption)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._populate_images.setText(self._app.localizer._("Populate images"))
        self._populate_images_caption.setText(
            self._app.localizer._(
                "Download images from the Wikipedia links in your ancestry"
            )
        )
