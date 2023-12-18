from __future__ import annotations

from typing import Any

from PyQt6 import QtGui
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QComboBox, QLabel, QWidget, QMainWindow, QMessageBox
from reactives.instance import ReactiveInstance
from reactives.instance.method import reactive_method

from betty.app import App
from betty.gui.text import Caption
from betty.locale import negotiate_locale, get_display_name


class TranslationsLocaleCollector(ReactiveInstance):
    def __init__(self, app: App, allowed_locales: set[str]):
        super().__init__()
        self._app = app
        self._allowed_locales = allowed_locales

        allowed_locale_names: list[tuple[str, str]] = []
        for allowed_locale in allowed_locales:
            locale_name = get_display_name(allowed_locale)
            if locale_name is not None:
                allowed_locale_names.append((
                    allowed_locale,
                    locale_name,
                ))
        allowed_locale_names = sorted(allowed_locale_names, key=lambda x: x[1])

        def _update_configuration_locale() -> None:
            self._app.configuration.locale = self._configuration_locale.currentData()
        self._configuration_locale = QComboBox()
        for i, (locale, locale_name) in enumerate(allowed_locale_names):
            self._configuration_locale.addItem(locale_name, locale)
            if locale == self._app.configuration.locale:
                self._configuration_locale.setCurrentIndex(i)
        self._configuration_locale.currentIndexChanged.connect(_update_configuration_locale)
        self._configuration_locale_label = QLabel()
        self._configuration_locale_caption = Caption()

        self._set_translatables()

    @property
    def locale(self) -> QComboBox:
        return self._configuration_locale

    @property
    def rows(self) -> list[list[Any]]:
        return [
            [self._configuration_locale_label, self._configuration_locale],
            [self._configuration_locale_caption],
        ]

    @reactive_method(on_trigger_call=True)
    def _set_translatables(self) -> None:
        self._configuration_locale_label.setText(self._app.localizer._('Locale'))
        locale = self.locale.currentData()
        if locale:
            translations_locale = negotiate_locale(
                locale,
                set(self._app.localizers.locales),
            )
            if translations_locale is None:
                self._configuration_locale_caption.setText(self._app.localizer._('There are no translations for {locale_name}.').format(
                    locale_name=get_display_name(locale, self._app.localizer.locale),
                ))
            else:
                negotiated_locale_translations_coverage = self._app.localizers.coverage(translations_locale)
                if negotiated_locale_translations_coverage[1] == 0:
                    negotiated_locale_translations_coverage_percentage = 0
                else:
                    negotiated_locale_translations_coverage_percentage = round(100 / (negotiated_locale_translations_coverage[1] / negotiated_locale_translations_coverage[0]))
                self._configuration_locale_caption.setText(self._app.localizer._('The translations for {locale_name} are {coverage_percentage}% complete.').format(
                    locale_name=get_display_name(translations_locale, self._app.localizer.locale),
                    coverage_percentage=round(negotiated_locale_translations_coverage_percentage)
                ))


class _LocalizedObject(ReactiveInstance):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._app = app

    def showEvent(  # type: ignore[misc]
        self: '_LocalizedObject' & QObject,
        event: QtGui.QShowEvent,
    ) -> None:
        super().showEvent(event)  # type: ignore[misc]
        self._set_translatables()

    @reactive_method(on_trigger_call=True)
    def _set_translatables(self) -> None:
        self._do_set_translatables()

    def _do_set_translatables(self) -> None:
        pass


class LocalizedWidget(  # type: ignore[misc]
    _LocalizedObject,
    QWidget,
):
    pass


class LocalizedMessageBox(  # type: ignore[misc]
    _LocalizedObject,
    QMessageBox,
):
    pass


class LocalizedWindow(  # type: ignore[misc]
    _LocalizedObject,
    QMainWindow,
):
    pass
