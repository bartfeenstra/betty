"""
Provide Cotton Candy's Graphical User Interface.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QPainter, QBrush, QColor, QPaintEvent
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QPushButton,
    QColorDialog,
    QHBoxLayout,
    QFormLayout,
    QWidget,
)
from typing_extensions import override

from betty.extension import CottonCandy, Webpack
from betty.extension.cotton_candy import _ColorConfiguration, CottonCandyConfiguration
from betty.gui.locale import LocalizedObject
from betty.gui.model import EntityReferenceSequenceCollector
from betty.gui.text import Caption
from betty.locale import Str, Localizable

if TYPE_CHECKING:
    from betty.app import App


class _ColorConfigurationSwatch(LocalizedObject, QWidget):
    def __init__(self, app: App, color: _ColorConfiguration, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)
        self._color = color
        self._color.on_change(self.repaint)
        self.setFixedHeight(24)
        self.setFixedWidth(24)
        self._swatch = QRect(self.rect())

    @override
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.fillRect(self._swatch, QBrush(QColor.fromString(self._color.hex)))
        painter.drawRect(self._swatch)


class _ColorConfigurationWidget(LocalizedObject, QWidget):
    def __init__(
        self,
        app: App,
        color: _ColorConfiguration,
        color_default: str,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(app, *args, **kwargs)
        self._color = color
        self._color_default = color_default
        self._layout = QHBoxLayout()
        self.setLayout(self._layout)

        self._label = QLabel()
        self._layout.addWidget(self._label)
        self._swatch = _ColorConfigurationSwatch(app, self._color)
        self._layout.addWidget(self._swatch)
        self._configure = QPushButton()
        self._layout.addWidget(self._configure)

        def _configure() -> None:
            qcolor = QColorDialog.getColor(initial=QColor.fromString(self._color.hex))
            if qcolor.isValid():
                self._color.hex = qcolor.name()

        self._configure.clicked.connect(_configure)
        self._reset = QPushButton()
        self._layout.addWidget(self._reset)

        def _reset() -> None:
            self._color.hex = self._color_default

        self._reset.clicked.connect(_reset)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._configure.setText(self._app.localizer._("Configure"))
        self._reset.setText(self._app.localizer._("Reset"))


class _ColorConfigurationsWidget(LocalizedObject, QWidget):
    def __init__(
        self,
        app: App,
        colors: list[tuple[_ColorConfiguration, Localizable, str]],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(app, *args, **kwargs)
        self._colors = colors
        self._color_configurations = []
        self._color_labels = []
        self._layout = QFormLayout()
        self.setLayout(self._layout)

        for color, __, color_default in colors:
            color_label = QLabel()
            self._color_labels.append(color_label)
            color_widget = _ColorConfigurationWidget(app, color, color_default)
            self._color_configurations.append(color_widget)
            self._layout.addRow(color_label, color_widget)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        for i, (__, color_label, ___) in enumerate(self._colors):
            self._color_labels[i].setText(color_label.localize(self._app.localizer))


class _CottonCandyGuiWidget(LocalizedObject, QWidget):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)
        self._app = app

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._color_configurations_widget = _ColorConfigurationsWidget(
            app,
            [
                (
                    app.extensions[CottonCandy].configuration.primary_inactive_color,
                    Str._("Primary color (inactive)"),
                    CottonCandyConfiguration.DEFAULT_PRIMARY_INACTIVE_COLOR,
                ),
                (
                    app.extensions[CottonCandy].configuration.primary_active_color,
                    Str._("Primary color (active)"),
                    CottonCandyConfiguration.DEFAULT_PRIMARY_ACTIVE_COLOR,
                ),
                (
                    app.extensions[CottonCandy].configuration.link_inactive_color,
                    Str._("Link color (inactive)"),
                    CottonCandyConfiguration.DEFAULT_LINK_INACTIVE_COLOR,
                ),
                (
                    app.extensions[CottonCandy].configuration.link_active_color,
                    Str._("Link color (active)"),
                    CottonCandyConfiguration.DEFAULT_LINK_ACTIVE_COLOR,
                ),
            ],
        )
        self._layout.addWidget(self._color_configurations_widget)
        self._color_configurations_widget_caption = Caption()
        self._layout.addWidget(self._color_configurations_widget_caption)
        if not self._app.extensions[Webpack].build_requirement().is_met():
            self._color_configurations_widget.setDisabled(True)
            self._color_configurations_widget_caption.setText(
                self._app.extensions[Webpack]
                .build_requirement()
                .localize(self._app.localizer)
            )

        self._featured_entities_label = QLabel()
        self._layout.addWidget(self._featured_entities_label)
        self._featured_entities_entity_references_collector = (
            EntityReferenceSequenceCollector(
                self._app,
                self._app.extensions[CottonCandy].configuration.featured_entities,
                Str._("Featured entities"),
                Str._("These entities are featured on your site's front page."),
            )
        )
        self._layout.addWidget(self._featured_entities_entity_references_collector)
