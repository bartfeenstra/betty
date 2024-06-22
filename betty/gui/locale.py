"""
Provide locale management for the Graphical User Interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PyQt6.QtWidgets import QComboBox, QLabel, QWidget

from betty.asyncio import wait_to_thread
from betty.gui.text import Caption
from betty.locale import negotiate_locale, get_display_name

if TYPE_CHECKING:
    from betty.app import App


class TranslationsLocaleCollector:
    """
    Helps users select a locale for which translations are available.
    """

    def __init__(self, app: App, allowed_locales: set[str]):
        self._app = app
        self._allowed_locales = allowed_locales

        allowed_locale_names: list[tuple[str, str]] = []
        for allowed_locale in allowed_locales:
            locale_name = get_display_name(allowed_locale)
            if locale_name is not None:
                allowed_locale_names.append(
                    (
                        allowed_locale,
                        locale_name,
                    )
                )
        allowed_locale_names = sorted(allowed_locale_names, key=lambda x: x[1])

        def _update_configuration_locale() -> None:
            self._app.configuration.locale = self.locale
            self._set_configuration_locale_caption()

        self._configuration_locale = QComboBox()
        for i, (locale, locale_name) in enumerate(allowed_locale_names):
            self._configuration_locale.addItem(locale_name, locale)
            if locale == self._app.configuration.locale:
                self._configuration_locale.setCurrentIndex(i)
        self._configuration_locale.currentIndexChanged.connect(
            _update_configuration_locale
        )
        self._configuration_locale_label = QLabel(self._app.localizer._("Locale"))
        self._configuration_locale_caption = Caption()

        self._set_configuration_locale_caption()

    def _set_configuration_locale_caption(self) -> None:
        locale = self.locale
        localizer = self._app.localizer
        localizers = self._app.localizers
        translations_locale = negotiate_locale(
            locale,
            list(localizers.locales),
        )
        if translations_locale is None:
            self._configuration_locale_caption.setText(
                localizer._("There are no translations for {locale_name}.").format(
                    locale_name=get_display_name(locale, localizer.locale),
                )
            )
        else:
            negotiated_locale_translations_coverage = wait_to_thread(
                localizers.coverage(translations_locale)
            )
            if negotiated_locale_translations_coverage[1] == 0:
                negotiated_locale_translations_coverage_percentage = 0
            else:
                negotiated_locale_translations_coverage_percentage = round(
                    100
                    / (
                        negotiated_locale_translations_coverage[1]
                        / negotiated_locale_translations_coverage[0]
                    )
                )
            self._configuration_locale_caption.setText(
                localizer._(
                    "The translations for {locale_name} are {coverage_percentage}%% complete."
                ).format(
                    locale_name=get_display_name(translations_locale, localizer.locale),
                    coverage_percentage=round(
                        negotiated_locale_translations_coverage_percentage
                    ),
                )
            )

    @property
    def locale(self) -> str:
        """
        The selected locale.
        """
        return cast(str, self._configuration_locale.currentData())

    @locale.setter
    def locale(self, locale: str) -> None:
        self._configuration_locale.setCurrentText(get_display_name(locale))

    @property
    def rows(self) -> list[list[QWidget]]:
        """
        The :py:class:`PyQt6.QtWidgets.QFormLayout` rows provided by the collector.
        """
        return [
            [self._configuration_locale_label, self._configuration_locale],
            [self._configuration_locale_caption],
        ]
