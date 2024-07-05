"""
Provide project administration for the Graphical User Interface.
"""

from __future__ import annotations

import asyncio
import copy
import re
from asyncio import Task, CancelledError
from contextlib import suppress, AsyncExitStack
from logging import getLogger
from pathlib import Path
from typing import final, TYPE_CHECKING
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QThread, QObject
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenu,
    QStackedLayout,
    QGridLayout,
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QButtonGroup,
    QRadioButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from babel import Locale
from babel.localedata import locale_identifiers
from typing_extensions import override

from betty import load, generate
from betty.asyncio import wait_to_thread
from betty.gui import (
    get_configuration_file_filter,
    GuiBuilder,
    mark_invalid,
    mark_valid,
)
from betty.gui.app import BettyPrimaryWindow
from betty.gui.error import ExceptionCatcher
from betty.gui.locale import LocalizedObject
from betty.gui.locale import TranslationsLocaleCollector
from betty.gui.logging import LogRecordViewerHandler, LogRecordViewer
from betty.gui.serve import ServeProjectWindow
from betty.gui.text import Text, Caption
from betty.gui.window import BettyMainWindow
from betty.locale import get_display_name, to_locale
from betty.locale.localizable import _, Localizable, plain
from betty.model import UserFacingEntity, Entity
from betty.project import LocaleConfiguration, Project, EntityTypeConfiguration
from betty.project.extension import UserFacingExtension
from betty.serde.load import AssertionFailed
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import MutableSequence


class _PaneButton(QPushButton):
    def __init__(self, pane_name: str, project_window: ProjectWindow):
        super().__init__()
        self.setFlat(True)
        self.setProperty("pane-selector", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed
        )
        self._project_window = project_window
        self.released.connect(lambda: self._project_window._navigate_to_pane(pane_name))


@final
@internal
class GenerateHtmlListForm(LocalizedObject, QWidget):
    """
    A form widget to configure whether to generate entity listing HTML pages for the project's entity types.
    """

    def __init__(self, project: Project):
        super().__init__(project.app)
        self._project = project
        self._form = QFormLayout()
        self.setLayout(self._form)
        self._form_label = QLabel()
        self._form.addRow(self._form_label)
        self._checkboxes_form = QFormLayout()
        self._form.addRow(self._checkboxes_form)
        self._checkboxes: dict[type[UserFacingEntity & Entity], QCheckBox] = {}
        self._update()

    def _update(self) -> None:
        entity_types = sorted(
            [
                entity_type
                for entity_type in self._project.entity_types
                if issubclass(entity_type, UserFacingEntity)
            ],
            key=lambda x: x.entity_type_label_plural().localize(self._app.localizer),
        )
        for entity_type in self._checkboxes:
            if entity_type not in entity_types:
                self._form.removeWidget(self._checkboxes[entity_type])
                del self._checkboxes[entity_type]
        for row_i, entity_type in enumerate(entity_types):
            self._update_for_entity_type(entity_type, row_i)

    def _update_for_entity_type(
        self, entity_type: type[UserFacingEntity & Entity], row_i: int
    ) -> None:
        if entity_type in self._checkboxes:
            self._checkboxes_form.insertRow(row_i, self._checkboxes[entity_type])
            return

        def _update(generate_html_list: bool) -> None:
            try:
                entity_type_configuration = self._project.configuration.entity_types[
                    entity_type
                ]
            except LookupError:
                entity_type_configuration = EntityTypeConfiguration(entity_type)
                self._project.configuration.entity_types.append(
                    (entity_type_configuration)
                )
            entity_type_configuration.generate_html_list = generate_html_list

        self._checkboxes[entity_type] = QCheckBox()
        self._checkboxes[entity_type].setChecked(
            entity_type in self._project.configuration.entity_types
            and self._project.configuration.entity_types[entity_type].generate_html_list
        )
        self._checkboxes[entity_type].toggled.connect(_update)
        self._update_for_entity_type(entity_type, row_i)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._form_label.setText(self._app.localizer._("Generate entity listing pages"))
        for entity_type in self._project.entity_types:
            if issubclass(entity_type, UserFacingEntity):
                self._checkboxes[entity_type].setText(
                    entity_type.entity_type_label_plural().localize(self._app.localizer)
                )


@final
@internal
class GeneralPane(LocalizedObject, QWidget):
    """
    A pane to administer general project configuration.
    """

    def __init__(self, project: Project):
        super().__init__(project.app)
        self._project = project

        self._form = QFormLayout()
        self.setLayout(self._form)
        self._build_name()
        self._build_title()
        self._build_author()
        self._build_url()
        self._build_lifetime_threshold()
        self._build_mode()
        self._build_clean_urls()
        self._generate_html_list_form = GenerateHtmlListForm(project)
        self._form.addRow(self._generate_html_list_form)

    def _build_name(self) -> None:
        def _update_configuration_name(name: str) -> None:
            self._project.configuration.name = name

        self._configuration_name = QLineEdit()
        self._configuration_name.setText(self._project.configuration.name)
        self._configuration_name.textChanged.connect(_update_configuration_name)
        self._configuration_name_label = QLabel()
        self._form.addRow(self._configuration_name_label, self._configuration_name)
        self._configuration_name_caption = Caption()
        self._form.addRow(self._configuration_name_caption)

    def _build_title(self) -> None:
        def _update_configuration_title(title: str) -> None:
            self._project.configuration.title = title

        self._configuration_title = QLineEdit()
        self._configuration_title.setText(self._project.configuration.title)
        self._configuration_title.textChanged.connect(_update_configuration_title)
        self._configuration_title_label = QLabel()
        self._form.addRow(self._configuration_title_label, self._configuration_title)

    def _build_author(self) -> None:
        def _update_configuration_author(author: str) -> None:
            self._project.configuration.author = author

        self._configuration_author = QLineEdit()
        self._configuration_author.setText(str(self._project.configuration.author))
        self._configuration_author.textChanged.connect(_update_configuration_author)
        self._configuration_author_label = QLabel()
        self._form.addRow(self._configuration_author_label, self._configuration_author)

    def _build_url(self) -> None:
        def _update_configuration_url(url: str) -> None:
            url_parts = urlparse(url)
            base_url = "%s://%s" % (url_parts.scheme, url_parts.netloc)
            root_path = url_parts.path
            configuration = copy.copy(self._project.configuration)
            try:
                configuration.base_url = base_url
                configuration.root_path = root_path
            except AssertionFailed as e:
                mark_invalid(self._configuration_url, str(e))
                return
            self._project.configuration.base_url = base_url
            self._project.configuration.root_path = root_path
            mark_valid(self._configuration_url)

        self._configuration_url = QLineEdit()
        self._configuration_url.setText(
            self._project.configuration.base_url + self._project.configuration.root_path
        )
        self._configuration_url.textChanged.connect(_update_configuration_url)
        self._configuration_url_label = QLabel()
        self._form.addRow(self._configuration_url_label, self._configuration_url)

    def _build_lifetime_threshold(self) -> None:
        def _update_configuration_lifetime_threshold(
            lifetime_threshold_value: str,
        ) -> None:
            if re.fullmatch(r"^\d+$", lifetime_threshold_value) is None:
                mark_invalid(
                    self._configuration_url,
                    self._app.localizer._(
                        "The lifetime threshold must consist of digits only."
                    ),
                )
                return
            lifetime_threshold = int(lifetime_threshold_value)
            try:
                self._project.configuration.lifetime_threshold = lifetime_threshold
                mark_valid(self._configuration_lifetime_threshold)
            except AssertionFailed as e:
                mark_invalid(self._configuration_lifetime_threshold, str(e))

        self._configuration_lifetime_threshold = QLineEdit()
        self._configuration_lifetime_threshold.setFixedWidth(32)
        self._configuration_lifetime_threshold.setText(
            str(self._project.configuration.lifetime_threshold)
        )
        self._configuration_lifetime_threshold.textChanged.connect(
            _update_configuration_lifetime_threshold
        )
        self._configuration_lifetime_threshold_label = QLabel()
        self._form.addRow(
            self._configuration_lifetime_threshold_label,
            self._configuration_lifetime_threshold,
        )
        self._configuration_lifetime_threshold_caption = Caption()
        self._form.addRow(self._configuration_lifetime_threshold_caption)

    def _build_mode(self) -> None:
        def _update_configuration_debug(mode: bool) -> None:
            self._project.configuration.debug = mode

        self._development_debug = QCheckBox()
        self._development_debug.setChecked(self._project.configuration.debug)
        self._development_debug.toggled.connect(_update_configuration_debug)
        self._form.addRow(self._development_debug)
        self._development_debug_caption = Caption()
        self._form.addRow(self._development_debug_caption)

    def _build_clean_urls(self) -> None:
        def _update_configuration_clean_urls(clean_urls: bool) -> None:
            self._project.configuration.clean_urls = clean_urls

        self._clean_urls = QCheckBox()
        self._clean_urls.setChecked(self._project.configuration.clean_urls)
        self._clean_urls.toggled.connect(_update_configuration_clean_urls)
        self._form.addRow(self._clean_urls)
        self._clean_urls_caption = Caption()
        self._form.addRow(self._clean_urls_caption)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._configuration_name_label.setText(self._app.localizer._("Name"))
        self._configuration_name_caption.setText(
            self._app.localizer._("The project's machine name.")
        )
        self._configuration_author_label.setText(self._app.localizer._("Author"))
        self._configuration_url_label.setText(self._app.localizer._("URL"))
        self._configuration_title_label.setText(self._app.localizer._("Title"))
        self._configuration_lifetime_threshold_label.setText(
            self._app.localizer._("Lifetime threshold")
        )
        self._configuration_lifetime_threshold_caption.setText(
            self._app.localizer._("The age at which people are presumed dead.")
        )
        self._development_debug.setText(self._app.localizer._("Debugging mode"))
        self._development_debug_caption.setText(
            self._app.localizer._(
                "Output more detailed logs and disable optimizations that make debugging harder."
            )
        )
        self._clean_urls.setText(self._app.localizer._("Clean URLs"))
        self._clean_urls_caption.setText(
            self._app.localizer._(
                "URLs look like <code>/path</code> instead of <code>/path/index.html</code>. This requires a web server that supports it."
            )
        )


@final
@internal
class LocalesConfigurationWidget(LocalizedObject, QWidget):
    """
    A form widget to configuration project locales.
    """

    def __init__(self, project: Project):
        super().__init__(project.app)
        self._project = project

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._locales_widget = QWidget()
        self._layout.addWidget(self._locales_widget)

        self._locales_layout = QGridLayout()
        self._locales_widget.setLayout(self._locales_layout)

        self._default_locale_heading = Text()
        self._locales_layout.addWidget(self._default_locale_heading)

        self._remove_buttons: dict[str, QPushButton] = {}
        self._default_buttons: dict[str, QRadioButton] = {}
        self._default_locale_button_group = QButtonGroup()

        self._add_locale_button = QPushButton()
        self._add_locale_button.released.connect(self._add_locale)
        self._layout.addWidget(self._add_locale_button)

        self._built_locales: MutableSequence[str] = []
        self._project.configuration.locales.on_change(
            self._rebuild_locales_configuration
        )
        self._rebuild_locales_configuration()

    def _rebuild_locales_configuration(self) -> None:
        built_locales = self._built_locales
        current_locales = [*self._project.configuration.locales]
        for built_locale in built_locales:
            if built_locale not in current_locales:
                self._remove_locale_configuration(built_locale)
        for row_index, current_locale in enumerate(
            sorted(
                current_locales,
                key=lambda locale: get_display_name(locale) or locale,
            )
        ):
            if current_locale not in built_locales:
                self._build_locale_configuration(current_locale)
            self._add_locale_configuration(current_locale, row_index)
        self._set_translatables()
        self._built_locales = current_locales

    def _add_locale_configuration(self, locale: str, row_index: int):
        self._locales_layout.addWidget(self._default_buttons[locale], row_index + 1, 0)
        self._locales_layout.addWidget(self._remove_buttons[locale], row_index + 1, 1)

        is_default = locale == self._project.configuration.locales.default.locale

        self._default_buttons[locale].setChecked(is_default)

        # Allow this locale configuration to be removed only if there are others, and if it is not default one.
        self._remove_buttons[locale].setEnabled(
            (len(self._project.configuration.locales) > 1 and not is_default)
        )

    def _remove_locale_configuration(self, locale: str) -> None:
        self._default_locale_button_group.removeButton(self._default_buttons[locale])
        self._locales_layout.removeWidget(self._default_buttons[locale])
        del self._default_buttons[locale]

        self._locales_layout.removeWidget(self._remove_buttons[locale])
        del self._remove_buttons[locale]

    def _build_locale_configuration(self, locale: str) -> None:
        self._default_buttons[locale] = QRadioButton()

        def _update_locales_configuration_default() -> None:
            self._project.configuration.locales.default = locale  # type: ignore[assignment]

        self._default_buttons[locale].clicked.connect(
            _update_locales_configuration_default
        )
        self._default_locale_button_group.addButton(self._default_buttons[locale])

        def _remove_locale() -> None:
            del self._project.configuration.locales[locale]

        remove_button = QPushButton()
        remove_button.released.connect(_remove_locale)
        self._remove_buttons[locale] = remove_button

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._default_locale_heading.setText(self._app.localizer._("Default locale"))
        self._add_locale_button.setText(self._app.localizer._("Add a locale"))
        for locale, button in self._default_buttons.items():
            button.setText(get_display_name(locale, self._app.localizer.locale))
        for button in self._remove_buttons.values():
            button.setText(self._app.localizer._("Remove"))

    def _add_locale(self) -> None:
        window = AddLocaleWindow(self._project, parent=self)
        window.show()


@final
@internal
class LocalizationPane(LocalizedObject, QWidget):
    """
    A pane for project localization configuration.
    """

    def __init__(self, project: Project):
        super().__init__(project.app)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._layout.addStretch()

        self._locales_configuration_widget = LocalesConfigurationWidget(project)
        self._layout.insertWidget(0, self._locales_configuration_widget)


@final
@internal
class AddLocaleWindow(BettyMainWindow):
    """
    A window to add a new project locale.
    """

    window_width = 500
    window_height = 250

    def __init__(
        self,
        project: Project,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(project.app, parent=parent)
        self._project = project

        self._layout = QFormLayout()
        self._widget = QWidget()
        self._widget.setLayout(self._layout)
        self.setCentralWidget(self._widget)

        self._locale_collector = TranslationsLocaleCollector(
            self._app,
            {
                to_locale(Locale.parse(babel_identifier))
                for babel_identifier in locale_identifiers()
            },
        )
        for row in self._locale_collector.rows:
            self._layout.addRow(*row)

        self._alias = QLineEdit()
        self._alias_label = QLabel()
        self._layout.addRow(self._alias_label, self._alias)
        self._alias_caption = Caption()
        self._layout.addRow(self._alias_caption)

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        self._save_and_close = QPushButton(self._app.localizer._("Save and close"))
        self._save_and_close.released.connect(self._save_and_close_locale)
        buttons_layout.addWidget(self._save_and_close)

        self._cancel = QPushButton(self._app.localizer._("Cancel"))
        self._cancel.released.connect(lambda _: self.close())
        buttons_layout.addWidget(self._cancel)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._alias_label.setText(self._app.localizer._("Alias"))
        self._alias_caption.setText(
            self._app.localizer._(
                "An optional alias is used instead of the locale code to identify this locale, such as in URLs. If US English is the only English language variant on your site, you may want to alias its language code from <code>en-US</code> to <code>en</code>, for instance."
            )
        )

    @override
    @property
    def window_title(self) -> Localizable:
        return _("Add a locale")

    def _save_and_close_locale(self) -> None:
        with ExceptionCatcher(self):
            locale = self._locale_collector.locale.currentData()
            alias: str | None = self._alias.text().strip()
            if alias == "":
                alias = None
            try:
                self._project.configuration.locales.append(
                    LocaleConfiguration(
                        locale,
                        alias=alias,
                    )
                )
            except AssertionFailed as e:
                mark_invalid(self._alias, str(e))
                return
            self.close()


@final
@internal
class ExtensionPane(LocalizedObject, QWidget):
    """
    A configuration pane for a single extension.
    """

    def __init__(self, project: Project, extension_type: type[UserFacingExtension]):
        super().__init__(project.app)
        self._project = project
        self._extension_type = extension_type

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        enable_layout = QFormLayout()
        layout.addLayout(enable_layout)

        self._extension_description = Text()
        enable_layout.addRow(self._extension_description)

        self._extension_gui: QWidget | None = None

        def _update_enabled(enabled: bool) -> None:
            with ExceptionCatcher(self):
                if enabled:
                    self._project.configuration.extensions.enable(extension_type)
                    extension = self._project.extensions[extension_type]
                    if isinstance(extension, GuiBuilder):
                        self._extension_gui = extension.gui_build()
                        layout.addWidget(self._extension_gui)
                else:
                    self._project.configuration.extensions.disable(extension_type)
                    if self._extension_gui is not None:
                        layout.removeWidget(self._extension_gui)
                        self._extension_gui.close()
                        self._extension_gui.setParent(None)
                        self._extension_gui.deleteLater()
                        self._extension_gui = None

        self._extension_enabled = QCheckBox()
        self._extension_enabled_caption = Caption()
        self._set_extension_status()
        self._extension_enabled.toggled.connect(_update_enabled)
        enable_layout.addRow(self._extension_enabled)
        enable_layout.addRow(self._extension_enabled_caption)

        if extension_type in self._project.extensions:
            extension = self._project.extensions[extension_type]
            if isinstance(extension, GuiBuilder):
                self._extension_gui = extension.gui_build()
                layout.addWidget(self._extension_gui)

    def _set_extension_status(self) -> None:
        self._extension_enabled.setDisabled(False)
        self._extension_enabled_caption.setText("")
        if self._extension_type in self._project.extensions:
            self._extension_enabled.setChecked(True)
            disable_requirement = self._project.extensions[
                self._extension_type
            ].disable_requirement()
            if not disable_requirement.is_met():
                self._extension_enabled.setDisabled(True)
                reduced_disable_requirement = disable_requirement.reduce()
                if reduced_disable_requirement is not None:
                    self._extension_enabled_caption.setText(
                        reduced_disable_requirement.localize(self._app.localizer)
                    )
        else:
            self._extension_enabled.setChecked(False)
            enable_requirement = self._extension_type.enable_requirement()
            if not enable_requirement.is_met():
                self._extension_enabled.setDisabled(True)
                reduced_enable_requirement = enable_requirement.reduce()
                if reduced_enable_requirement is not None:
                    self._extension_enabled_caption.setText(
                        reduced_enable_requirement.localize(self._app.localizer)
                    )

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._extension_description.setText(
            self._extension_type.description().localize(self._app.localizer)
        )
        self._extension_enabled.setText(
            self._app.localizer._("Enable {extension}").format(
                extension=self._extension_type.label().localize(self._app.localizer),
            )
        )


@final
class ProjectWindow(BettyPrimaryWindow):
    """
    A window to administer a project.
    """

    def __init__(self, project: Project):
        """
        :param project: The project must not be bootstrapped yet, and will be owned by the window.
        """
        super().__init__(project.app)
        self._async_exit_stack = AsyncExitStack()
        self._project = project
        self._built = False

    def _bootstrap(self) -> None:
        if not self._built:
            wait_to_thread(self._async_exit_stack.enter_async_context(self._project))

            central_widget = QWidget()
            central_layout = QHBoxLayout()
            central_widget.setLayout(central_layout)
            self.setCentralWidget(central_widget)

            self._pane_selectors_container_widget = QWidget()
            self._pane_selectors_container_widget.setFixedWidth(225)

            self._pane_selectors_container = QScrollArea()
            self._pane_selectors_container.setFrameShape(QFrame.Shape.NoFrame)
            self._pane_selectors_container.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self._pane_selectors_container.setWidget(
                self._pane_selectors_container_widget
            )
            self._pane_selectors_container.setWidgetResizable(True)
            self._pane_selectors_container.setFixedWidth(225)
            central_layout.addWidget(self._pane_selectors_container)

            self._pane_selectors_layout = QVBoxLayout()
            self._pane_selectors_layout.setContentsMargins(0, 0, 25, 0)
            self._pane_selectors_container_widget.setLayout(self._pane_selectors_layout)

            self._builtin_pane_selectors_layout = QVBoxLayout()
            self._pane_selectors_layout.addLayout(self._builtin_pane_selectors_layout)

            pane_selectors_divider = QFrame()
            pane_selectors_divider.setFrameShape(QFrame.Shape.HLine)
            pane_selectors_divider.setFrameShadow(QFrame.Shadow.Sunken)
            self._pane_selectors_layout.addWidget(pane_selectors_divider)

            self._extension_pane_selectors_layout = QVBoxLayout()
            self._pane_selectors_layout.addLayout(self._extension_pane_selectors_layout)

            self._pane_selectors_layout.addStretch()

            self._panes_layout = QStackedLayout()
            central_layout.addLayout(self._panes_layout, 999999999)

            self._panes: dict[str, QWidget] = {}
            self._pane_containers: dict[str, QWidget] = {}
            self._pane_selectors: dict[str, QPushButton] = {}

            self._add_pane("general", GeneralPane(self._project))
            self._builtin_pane_selectors_layout.addWidget(
                self._pane_selectors["general"]
            )
            self._navigate_to_pane("general")
            self._add_pane("localization", LocalizationPane(self._project))
            self._builtin_pane_selectors_layout.addWidget(
                self._pane_selectors["localization"]
            )
            self._extension_types = [
                extension_type
                for extension_type in self._project.discover_extension_types()
                if issubclass(extension_type, UserFacingExtension)
            ]
            for extension_type in self._extension_types:
                self._add_pane(
                    f"extension-{extension_type.name()}",
                    ExtensionPane(self._project, extension_type),
                )

            menu_bar = self.menuBar()
            assert menu_bar is not None

            self.project_menu = QMenu()
            menu_bar.addMenu(self.project_menu)
            menu_bar.insertMenu(self.help_menu.menuAction(), self.project_menu)

            self.save_project_as_action = QAction(self)
            self.save_project_as_action.setShortcut("Ctrl+Shift+S")
            self.save_project_as_action.triggered.connect(
                lambda _: self.save_project_as(),
            )
            self.project_menu.addAction(self.save_project_as_action)

            self.generate_action = QAction(self)
            self.generate_action.setShortcut("Ctrl+G")
            self.generate_action.triggered.connect(
                lambda _: self.generate(),
            )
            self.project_menu.addAction(self.generate_action)

            self.serve_action = QAction(self)
            self.serve_action.setShortcut("Ctrl+Alt+S")
            self.serve_action.triggered.connect(
                lambda _: self.serve(),
            )
            self.project_menu.addAction(self.serve_action)

            self._built = True

    def _add_pane(self, pane_name: str, pane: QWidget) -> None:
        pane_container = QScrollArea()
        pane_container.setFrameShape(QFrame.Shape.NoFrame)
        pane_container.setWidget(pane)
        pane_container.setWidgetResizable(True)
        pane.setMinimumWidth(300)
        pane.setMaximumWidth(1000)
        self._pane_containers[pane_name] = pane_container
        self._panes[pane_name] = pane
        self._panes_layout.addWidget(pane_container)
        self._pane_selectors[pane_name] = _PaneButton(pane_name, self)

    def _navigate_to_pane(self, pane_name: str) -> None:
        for pane_selector in self._pane_selectors.values():
            pane_selector.setFlat(True)
        self._pane_selectors[pane_name].setFlat(False)
        self._panes_layout.setCurrentWidget(self._pane_containers[pane_name])

    @override
    def show(self) -> None:
        self._bootstrap()
        self._project.configuration.autowrite = True
        super().show()

    @override
    def close(self) -> bool:
        self._project.configuration.autowrite = False
        wait_to_thread(self._async_exit_stack.aclose())
        return super().close()

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self.project_menu.setTitle("&" + self._app.localizer._("Project"))
        self.save_project_as_action.setText(
            self._app.localizer._("Save this project as...")
        )
        self.generate_action.setText(self._app.localizer._("Generate site"))
        self.serve_action.setText(self._app.localizer._("Serve site"))
        self._pane_selectors["general"].setText(self._app.localizer._("General"))
        self._pane_selectors["localization"].setText(
            self._app.localizer._("Localization")
        )

        # Sort extension pane selector buttons by their human-readable label.
        extension_pane_selector_labels = [
            (extension_type, extension_type.label().localize(self._app.localizer))
            for extension_type in self._extension_types
        ]
        for extension_type, _extension_label in sorted(
            extension_pane_selector_labels, key=lambda x: x[1]
        ):
            extension_pane_name = f"extension-{extension_type.name()}"
            self._pane_selectors[extension_pane_name].setText(
                extension_type.label().localize(self._app.localizer)
            )
            self._extension_pane_selectors_layout.addWidget(
                self._pane_selectors[extension_pane_name]
            )

    @override
    @property
    def window_title(self) -> Localizable:
        return plain(self._project.configuration.title)

    def save_project_as(self) -> None:
        """
        Copy this project and save it as a new one.
        """
        with ExceptionCatcher(self):
            configuration_file_path_str, __ = QFileDialog.getSaveFileName(
                self,
                self._app.localizer._("Save your project to..."),
                "",
                get_configuration_file_filter().localize(self._app.localizer),
            )
            wait_to_thread(
                self._project.configuration.write(Path(configuration_file_path_str))
            )

    def generate(self) -> None:
        """
        Generate a site for the project.
        """
        with ExceptionCatcher(self):
            generate_window = GenerateWindow(self._project, parent=self)
            generate_window.show()

    def serve(self) -> None:
        """
        Serve the project's generated site.
        """
        with ExceptionCatcher(self):
            serve_window = ServeProjectWindow(self._project, parent=self)
            serve_window.show()


class _GenerateThread(QThread):
    def __init__(self, project: Project, generate_window: GenerateWindow):
        super().__init__()
        self._project = project
        self._generate_window = generate_window
        self._task: Task[None] | None = None

    @override
    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        with suppress(CancelledError):
            self._task = asyncio.create_task(self._generate())
            await self._task

    async def _generate(self) -> None:
        with ExceptionCatcher(self._generate_window, close_parent=True):
            await load.load(self._project)
            await generate.generate(self._project)

    def cancel(self) -> None:
        if self._task:
            self._task.cancel()


@final
@internal
class GenerateWindow(BettyMainWindow):
    """
    A window to control a site generation job.
    """

    window_width = 500
    window_height = 100

    def __init__(
        self,
        project: Project,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(project.app, parent=parent)
        self._project = project

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowCloseButtonHint)

        central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self._log_record_viewer = LogRecordViewer()
        central_layout.addWidget(self._log_record_viewer)

        button_layout = QHBoxLayout()
        central_layout.addLayout(button_layout)

        self._cancel_button = QPushButton()
        self._cancel_button.released.connect(self.close)
        button_layout.addWidget(self._cancel_button)

        self._serve_button = QPushButton()
        self._serve_button.setDisabled(True)
        self._serve_button.released.connect(self._serve)
        button_layout.addWidget(self._serve_button)

        self._log_record_viewer = LogRecordViewer()
        central_layout.addWidget(self._log_record_viewer)

        self._logging_handler = LogRecordViewerHandler(self._log_record_viewer)
        getLogger(__name__).addHandler(self._logging_handler)

        self._thread = _GenerateThread(self._project, self)
        self._thread.finished.connect(self._finish_generate)
        self._thread.start()

    @override
    @property
    def window_title(self) -> Localizable:
        return _("Generating your site...")

    def _serve(self) -> None:
        with ExceptionCatcher(self):
            serve_window = ServeProjectWindow(self._project, parent=self.parent())
            serve_window.show()

    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        super().closeEvent(a0)
        self._thread.cancel()
        self._finalize()

    def _finish_generate(self) -> None:
        self._cancel_button.setDisabled(True)
        self._serve_button.setDisabled(False)
        self._finalize()

    def _finalize(self) -> None:
        getLogger(__name__).removeHandler(self._logging_handler)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._cancel_button.setText(self._app.localizer._("Cancel"))
        self._cancel_button.setText(self._app.localizer._("Cancel"))
        self._serve_button.setText(self._app.localizer._("View site"))
