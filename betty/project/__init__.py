"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

import operator
from contextlib import suppress, asynccontextmanager
from functools import reduce
from graphlib import TopologicalSorter, CycleError
from pathlib import Path
from reprlib import recursive_repr
from typing import Any, Generic, final, Iterable, cast, Self, TYPE_CHECKING, TypeVar
from urllib.parse import urlparse

from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty import fs
from betty.assets import AssetRepository
from betty.asyncio import wait_to_thread
from betty.classtools import repr_instance
from betty.config import (
    Configuration,
    Configurable,
    FileBasedConfiguration,
    ConfigurationMapping,
    ConfigurationSequence,
)
from betty.core import CoreComponent
from betty.hashid import hashid
from betty.locale import DEFAULT_LOCALE, LocalizerRepository
from betty.locale.localizable import _
from betty.model import (
    Entity,
    get_entity_type_name,
    UserFacingEntity,
    EntityTypeProvider,
)
from betty.model.ancestry import Ancestry, Person, Event, Place, Source
from betty.model.event_type import (
    EventType,
    EventTypeProvider,
    Birth,
    Baptism,
    Adoption,
    Death,
    Funeral,
    Cremation,
    Burial,
    Will,
    Engagement,
    Marriage,
    MarriageAnnouncement,
    Divorce,
    DivorceAnnouncement,
    Residence,
    Immigration,
    Emigration,
    Occupation,
    Retirement,
    Correspondence,
    Confirmation,
)
from betty.project.extension import (
    Extension,
    ConfigurableExtension,
    build_extension_type_graph,
    CyclicDependencyError,
    Extensions,
    ListExtensions,
    ExtensionDispatcher,
)
from betty.render import Renderer, SequentialRenderer
from betty.serde.dump import (
    Dump,
    VoidableDump,
    void_none,
    minimize,
    VoidableDictDump,
)
from betty.typing import Void
from betty.assertion import (
    Assertion,
    RequiredField,
    OptionalField,
    assert_record,
    assert_entity_type,
    assert_setattr,
    assert_str,
    assert_extension_type,
    assert_bool,
    assert_dict,
    assert_locale,
    assert_int,
    assert_positive_number,
    assert_fields,
)
from betty.assertion.error import AssertionFailed

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from betty.app import App
    from betty.dispatch import Dispatcher
    from betty.url import LocalizedUrlGenerator, StaticUrlGenerator
    from betty.jinja2 import Environment


_EntityT = TypeVar("_EntityT", bound=Entity)


#: The default age by which people are presumed dead.
DEFAULT_LIFETIME_THRESHOLD = 125


class EntityReference(Configuration, Generic[_EntityT]):
    """
    Configuration that references an entity from the project's ancestry.
    """

    def __init__(
        self,
        entity_type: type[_EntityT] | None = None,
        entity_id: str | None = None,
        *,
        entity_type_is_constrained: bool = False,
    ):
        super().__init__()
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._entity_type_is_constrained = entity_type_is_constrained

    @property
    def entity_type(self) -> type[_EntityT] | None:
        """
        The referenced entity's type.
        """
        return self._entity_type

    @entity_type.setter
    def entity_type(self, entity_type: type[_EntityT]) -> None:
        if self._entity_type_is_constrained:
            raise AttributeError(
                f"The entity type cannot be set, as it is already constrained to {self._entity_type}."
            )
        self._entity_type = entity_type
        self._dispatch_change()

    @property
    def entity_id(self) -> str | None:
        """
        The referenced entity's ID.
        """
        return self._entity_id

    @entity_id.setter
    def entity_id(self, entity_id: str) -> None:
        self._entity_id = entity_id
        self._dispatch_change()

    @entity_id.deleter
    def entity_id(self) -> None:
        self._entity_id = None

    @property
    def entity_type_is_constrained(self) -> bool:
        """
        Whether the entity type may be changed.
        """
        return self._entity_type_is_constrained

    @override
    def update(self, other: Self) -> None:
        self._entity_type = other._entity_type
        self._entity_type_is_constrained = other._entity_type_is_constrained
        self._entity_id = other._entity_id
        self._dispatch_change()

    @override
    def load(
        self,
        dump: Dump,
    ) -> None:
        if isinstance(dump, dict) or not self.entity_type_is_constrained:
            assert_record(
                RequiredField(
                    "entity_type",
                    assert_entity_type() | assert_setattr(self, "entity_type"),
                ),
                OptionalField(
                    "entity_id",
                    assert_str() | assert_setattr(self, "entity_id"),
                ),
            )(dump)
        else:
            assert_str()(dump)
            assert_setattr(self, "entity_id")(dump)

    @override
    def dump(self) -> VoidableDump:
        if self.entity_type_is_constrained:
            return void_none(self.entity_id)

        if self.entity_type is None or self.entity_id is None:
            return Void

        dump: VoidableDictDump[VoidableDump] = {
            "entity_type": (
                get_entity_type_name(self._entity_type) if self._entity_type else Void
            ),
            "entity_id": self._entity_id,
        }

        return minimize(dump)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EntityReference):
            return NotImplemented
        return (
            self.entity_type == other.entity_type and self.entity_id == other.entity_id
        )


class EntityReferenceSequence(
    Generic[_EntityT], ConfigurationSequence[EntityReference[_EntityT]]
):
    """
    Configuration for a sequence of references to entities from the project's ancestry.
    """

    def __init__(
        self,
        entity_references: Iterable[EntityReference[_EntityT]] | None = None,
        *,
        entity_type_constraint: type[_EntityT] | None = None,
    ):
        self._entity_type_constraint = entity_type_constraint
        super().__init__(entity_references)

    @override
    def load_item(self, dump: Dump) -> EntityReference[_EntityT]:
        configuration = EntityReference[_EntityT](
            # Use a dummy entity type for now to satisfy the initializer.
            # It will be overridden when loading the dump.
            Entity  # type: ignore[arg-type]
            if self._entity_type_constraint is None
            else self._entity_type_constraint,
            entity_type_is_constrained=self._entity_type_constraint is not None,
        )
        configuration.load(dump)
        return configuration

    @override
    def _on_add(self, configuration: EntityReference[_EntityT]) -> None:
        super()._on_add(configuration)

        entity_type_constraint = self._entity_type_constraint
        entity_reference_entity_type = configuration._entity_type

        if entity_type_constraint is None:
            configuration._entity_type_is_constrained = False
            return

        configuration._entity_type_is_constrained = True

        if (
            entity_reference_entity_type == entity_type_constraint
            and configuration.entity_type_is_constrained
        ):
            return

        expected_entity_type_name = get_entity_type_name(
            cast(type[Entity], entity_type_constraint),
        )
        expected_entity_type_label = entity_type_constraint.entity_type_label()

        if entity_reference_entity_type is None:
            raise AssertionFailed(
                _(
                    "The entity reference must be for an entity of type {expected_entity_type_name} ({expected_entity_type_label}), but instead does not specify an entity type at all."
                ).format(
                    expected_entity_type_name=expected_entity_type_name,
                    expected_entity_type_label=expected_entity_type_label,
                )
            )

        actual_entity_type_label = entity_type_constraint.entity_type_label()

        raise AssertionFailed(
            _(
                "The entity reference must be for an entity of type {expected_entity_type_name} ({expected_entity_type_label}), but instead is for an entity of type {actual_entity_type_name} ({actual_entity_type_label})"
            ).format(
                expected_entity_type_name=expected_entity_type_name,
                expected_entity_type_label=expected_entity_type_label,
                actual_entity_type_name=get_entity_type_name(
                    entity_reference_entity_type
                ),
                actual_entity_type_label=actual_entity_type_label,
            )
        )


class ExtensionConfiguration(Configuration):
    """
    Configure a single extension for a project.
    """

    def __init__(
        self,
        extension_type: type[Extension],
        *,
        enabled: bool = True,
        extension_configuration: Configuration | None = None,
    ):
        super().__init__()
        self._extension_type = extension_type
        self._enabled = enabled
        if extension_configuration is None and issubclass(
            extension_type, ConfigurableExtension
        ):
            extension_configuration = extension_type.default_configuration()
        self._set_extension_configuration(extension_configuration)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.extension_type != other.extension_type:
            return False
        if self.enabled != other.enabled:
            return False
        if self.extension_configuration != other.extension_configuration:
            return False
        return True

    @property
    def extension_type(self) -> type[Extension]:
        """
        The extension type.
        """
        return self._extension_type

    @property
    def enabled(self) -> bool:
        """
        Whether the extension is enabled.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._dispatch_change()

    @property
    def extension_configuration(self) -> Configuration | None:
        """
        Get the extension's own configuration.
        """
        return self._extension_configuration

    def _set_extension_configuration(
        self, extension_configuration: Configuration | None
    ) -> None:
        if extension_configuration is not None:
            extension_configuration.on_change(self)
        self._extension_configuration = extension_configuration

    @override
    def update(self, other: Self) -> None:
        self._extension_type = other._extension_type
        self._enabled = other._enabled
        self._set_extension_configuration(other._extension_configuration)

    @classmethod
    def assert_load(cls) -> Assertion[Dump, ExtensionConfiguration]:
        """
        Build an assertion to create a new instance and load a configuration dump into it.
        """

        def _assertion(dump: Dump) -> ExtensionConfiguration:
            dict_dump = assert_fields(
                RequiredField("extension", assert_extension_type())
            )(dump)
            configuration = cls(dict_dump["extension"])
            configuration.load(dump)
            return configuration

        return _assertion

    _extension_type_assertion = assert_extension_type()

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField(
                "extension",
                self._extension_type_assertion
                | assert_setattr(self, "_extension_type"),
            ),
            OptionalField("enabled", assert_bool() | assert_setattr(self, "enabled")),
            OptionalField(
                "configuration",
                self._assert_load_extension_configuration(self.extension_type),
            ),
        )(dump)

    def _assert_load_extension_configuration(
        self, extension_type: type[Extension]
    ) -> Assertion[Any, Configuration]:
        def _assertion(value: Any) -> Configuration:
            extension_configuration = self._extension_configuration
            if isinstance(extension_configuration, Configuration):
                extension_configuration.load(value)
                return extension_configuration
            raise AssertionFailed(
                _("{extension_type} is not configurable.").format(
                    extension_type=extension_type.name()
                )
            )

        return _assertion

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            {
                "extension": self.extension_type.name(),
                "enabled": self.enabled,
                "configuration": (
                    minimize(self.extension_configuration.dump())
                    if issubclass(self.extension_type, Configurable)
                    and self.extension_configuration
                    else Void
                ),
            }
        )


class ExtensionConfigurationMapping(
    ConfigurationMapping[type[Extension], ExtensionConfiguration]
):
    """
    Configure a project's extensions.
    """

    @override
    def _minimize_item_dump(self) -> bool:
        return True

    def __init__(
        self,
        configurations: Iterable[ExtensionConfiguration] | None = None,
    ):
        super().__init__(configurations)

    @override
    def load_item(self, dump: Dump) -> ExtensionConfiguration:
        return ExtensionConfiguration.assert_load()(dump)

    @override
    def _get_key(self, configuration: ExtensionConfiguration) -> type[Extension]:
        return configuration.extension_type

    @override
    def _load_key(
        self,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        dict_dump = assert_dict()(item_dump)
        dict_dump["extension"] = key_dump
        return dict_dump

    @override
    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dict_dump = assert_dict()(item_dump)
        return dict_dump, dict_dump.pop("extension")

    def enable(self, *extension_types: type[Extension]) -> None:
        """
        Enable the given extensions.
        """
        for extension_type in extension_types:
            try:
                self._configurations[extension_type].enabled = True
            except KeyError:
                self.append(ExtensionConfiguration(extension_type))

    def disable(self, *extension_types: type[Extension]) -> None:
        """
        Disable the given extensions.
        """
        for extension_type in extension_types:
            with suppress(KeyError):
                self._configurations[extension_type].enabled = False


class EntityTypeConfiguration(Configuration):
    """
    Configure a single entity type for a project.
    """

    def __init__(
        self,
        entity_type: type[Entity],
        *,
        generate_html_list: bool | None = None,
    ):
        super().__init__()
        self._entity_type = entity_type
        self.generate_html_list = generate_html_list  # type: ignore[assignment]

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.entity_type != other.entity_type:
            return False
        if self.generate_html_list != other.generate_html_list:
            return False
        return True

    @property
    def entity_type(self) -> type[Entity]:
        """
        The configured entity type.
        """
        return self._entity_type

    @property
    def generate_html_list(self) -> bool:
        """
        Whether to generate listing web pages for entities of this type.
        """
        return self._generate_html_list or False

    @generate_html_list.setter
    def generate_html_list(self, generate_html_list: bool | None) -> None:
        if generate_html_list and not issubclass(self._entity_type, UserFacingEntity):
            raise AssertionFailed(
                _(
                    "Cannot generate pages for {entity_type}, because it is not a user-facing entity type."
                ).format(entity_type=get_entity_type_name(self._entity_type))
            )
        self._generate_html_list = generate_html_list
        self._dispatch_change()

    @override
    def update(self, other: Self) -> None:
        self._entity_type = other._entity_type
        self._generate_html_list = other._generate_html_list
        self._dispatch_change()

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField[Any, type[Entity]](
                "entity_type",
                assert_str()
                | assert_entity_type()
                | assert_setattr(self, "_entity_type"),
            ),
            OptionalField(
                "generate_html_list",
                assert_bool() | assert_setattr(self, "generate_html_list"),
            ),
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        dump: VoidableDictDump[VoidableDump] = {
            "entity_type": get_entity_type_name(self._entity_type),
            "generate_html_list": (
                Void if self._generate_html_list is None else self._generate_html_list
            ),
        }

        return minimize(dump)


class EntityTypeConfigurationMapping(
    ConfigurationMapping[type[Entity], EntityTypeConfiguration]
):
    """
    Configure the entity types for a project.
    """

    @override
    def _minimize_item_dump(self) -> bool:
        return True

    @override
    def _get_key(self, configuration: EntityTypeConfiguration) -> type[Entity]:
        return configuration.entity_type

    @override
    def _load_key(
        self,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        dict_dump = assert_dict()(item_dump)
        assert_entity_type()(key_dump)
        dict_dump["entity_type"] = key_dump
        return dict_dump

    @override
    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dict_dump = assert_dict()(item_dump)
        return dict_dump, dict_dump.pop("entity_type")

    @override
    def load_item(self, dump: Dump) -> EntityTypeConfiguration:
        # Use a dummy entity type for now to satisfy the initializer.
        # It will be overridden when loading the dump.
        configuration = EntityTypeConfiguration(Entity)
        configuration.load(dump)
        return configuration


class LocaleConfiguration(Configuration):
    """
    Configure a single project locale.
    """

    def __init__(
        self,
        locale: str,
        *,
        alias: str | None = None,
    ):
        super().__init__()
        self._locale = locale
        if alias is not None and "/" in alias:
            raise AssertionFailed(_("Locale aliases must not contain slashes."))
        self._alias = alias

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, locale=self.locale, alias=self.alias)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.locale != other.locale:
            return False
        if self.alias != other.alias:
            return False
        return True

    @override
    def __hash__(self) -> int:
        return hash((self._locale, self._alias))

    @property
    def locale(self) -> str:
        """
        An `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
        """
        return self._locale

    @property
    def alias(self) -> str:
        """
        A shorthand alias to use instead of the full language tag, such as when rendering URLs.
        """
        if self._alias is None:
            return self.locale
        return self._alias

    @alias.setter
    def alias(self, alias: str | None) -> None:
        self._alias = alias
        self._dispatch_change()

    @override
    def update(self, other: Self) -> None:
        self._locale = other._locale
        self._alias = other._alias

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("locale", assert_locale() | assert_setattr(self, "_locale")),
            OptionalField("alias", assert_str() | assert_setattr(self, "alias")),
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return minimize({"locale": self.locale, "alias": void_none(self._alias)})


class LocaleConfigurationMapping(ConfigurationMapping[str, LocaleConfiguration]):
    """
    Configure a project's locales.
    """

    def __init__(
        self,
        configurations: Iterable[LocaleConfiguration] | None = None,
    ):
        super().__init__(configurations)
        self._ensure_locale()

    @override
    def _on_remove(self, configuration: LocaleConfiguration) -> None:
        super()._on_remove(configuration)
        self._ensure_locale()

    def _ensure_locale(self) -> None:
        if len(self) == 0:
            self.append(LocaleConfiguration(DEFAULT_LOCALE))

    @override
    def _get_key(self, configuration: LocaleConfiguration) -> str:
        return configuration.locale

    @override
    def _load_key(
        self,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        dict_item_dump = assert_dict()(item_dump)
        dict_item_dump["locale"] = key_dump
        return dict_item_dump

    @override
    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dict_item_dump = assert_dict()(item_dump)
        return dict_item_dump, dict_item_dump.pop("locale")

    @override
    def load_item(self, dump: Dump) -> LocaleConfiguration:
        item = LocaleConfiguration("und")
        item.load(dump)
        return item

    @property
    def default(self) -> LocaleConfiguration:
        """
        The default language.
        """
        return next(iter(self._configurations.values()))

    @default.setter
    def default(self, configuration: LocaleConfiguration | str) -> None:
        if isinstance(configuration, str):
            configuration = self[configuration]
        self._configurations[configuration.locale] = configuration
        self._configurations.move_to_end(configuration.locale, False)
        self._dispatch_change()

    @property
    def multilingual(self) -> bool:
        """
        Whether the configuration is multilingual.
        """
        return len(self) > 1


@final
class ProjectConfiguration(FileBasedConfiguration):
    """
    Provide the configuration for a :py:class:`betty.project.Project`.
    """

    def __init__(
        self,
        configuration_file_path: Path,
        *,
        base_url: str | None = None,
        root_path: str = "",
        clean_urls: bool = False,
        title: str = "Betty",
        author: str | None = None,
        entity_types: Iterable[EntityTypeConfiguration] | None = None,
        extensions: Iterable[ExtensionConfiguration] | None = None,
        debug: bool = False,
        locales: Iterable[LocaleConfiguration] | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        name: str | None = None,
    ):
        super().__init__(configuration_file_path)
        self._name = name
        self._computed_name: str | None = None
        self._base_url = "https://example.com" if base_url is None else base_url
        self._root_path = root_path
        self._clean_urls = clean_urls
        self._title = title
        self._author = author
        self._entity_types = EntityTypeConfigurationMapping(
            entity_types
            or [
                EntityTypeConfiguration(
                    entity_type=Person,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=Event,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=Place,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=Source,
                    generate_html_list=True,
                ),
            ]
        )
        self._entity_types.on_change(self)
        self._extensions = ExtensionConfigurationMapping(extensions or ())
        self._extensions.on_change(self)
        self._debug = debug
        self._locales = LocaleConfigurationMapping(locales or ())
        self._locales.on_change(self)
        self._lifetime_threshold = lifetime_threshold

    @property
    def name(self) -> str | None:
        """
        The project's machine name.
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name
        self._dispatch_change()

    @property
    def project_directory_path(self) -> Path:
        """
        The project directory path.

        Betty will look for resources in this directory, and place generated artifacts there. It is expected
        that no other applications or projects share this same directory.
        """
        return self.configuration_file_path.parent

    @property
    def output_directory_path(self) -> Path:
        """
        The output directory path.
        """
        return self.project_directory_path / "output"

    @property
    def assets_directory_path(self) -> Path:
        """
        The :doc:`assets directory path </usage/assets>`.
        """
        return self.project_directory_path / "assets"

    @property
    def www_directory_path(self) -> Path:
        """
        The WWW directory path.
        """
        return self.output_directory_path / "www"

    def localize_www_directory_path(self, locale: str) -> Path:
        """
        Get the WWW directory path for a locale.
        """
        if self.locales.multilingual:
            return self.www_directory_path / self.locales[locale].alias
        return self.www_directory_path

    @property
    def title(self) -> str:
        """
        The project's human-readable title.
        """
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title
        self._dispatch_change()

    @property
    def author(self) -> str | None:
        """
        The project's author.
        """
        return self._author

    @author.setter
    def author(self, author: str | None) -> None:
        self._author = author
        self._dispatch_change()

    @property
    def base_url(self) -> str:
        """
        The project's public URL's base URL.

        If the public URL is ``https://example.com``, the base URL is ``https://example.com``.
        If the public URL is ``https://example.com/my-ancestry-site``, the base URL is ``https://example.com``.
        If the public URL is ``https://my-ancestry-site.example.com``, the base URL is ``https://my-ancestry-site.example.com``.
        """
        return self._base_url

    @base_url.setter
    def base_url(self, base_url: str) -> None:
        base_url_parts = urlparse(base_url)
        if not base_url_parts.scheme:
            raise AssertionFailed(
                _(
                    "The base URL must start with a scheme such as https://, http://, or file://."
                )
            )
        if not base_url_parts.netloc:
            raise AssertionFailed(_("The base URL must include a path."))
        self._base_url = "%s://%s" % (base_url_parts.scheme, base_url_parts.netloc)
        self._dispatch_change()

    @property
    def root_path(self) -> str:
        """
        The project's public URL's root path.

        If the public URL is ``https://example.com``, the root path is an empty string.
        If the public URL is ``https://example.com/my-ancestry-site``, the root path is ``/my-ancestry-site``.
        """
        return self._root_path

    @root_path.setter
    def root_path(self, root_path: str) -> None:
        self._root_path = root_path.strip("/")
        self._dispatch_change()

    @property
    def clean_urls(self) -> bool:
        """
        Whether to generate clean URLs such as ``/person/first-person`` instead of ``/person/first-person/index.html``.

        Generated artifacts will require web server that supports this.
        """
        return self._clean_urls

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool) -> None:
        self._clean_urls = clean_urls
        self._dispatch_change()

    @property
    def locales(self) -> LocaleConfigurationMapping:
        """
        The available locales.
        """
        return self._locales

    @property
    def entity_types(self) -> EntityTypeConfigurationMapping:
        """
        The available entity types.
        """
        return self._entity_types

    @property
    def extensions(self) -> ExtensionConfigurationMapping:
        """
        Then extensions running within this application.
        """
        return self._extensions

    @property
    def debug(self) -> bool:
        """
        Whether to enable debugging for project jobs.

        This setting is disabled by default.

        Enabling this generally results in:

        - More verbose logging output
        - job artifacts (e.g. generated sites)
        """
        return self._debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._debug = debug
        self._dispatch_change()

    @property
    def lifetime_threshold(self) -> int:
        """
        The lifetime threshold indicates when people are considered dead.

        This setting defaults to :py:const:`betty.project.DEFAULT_LIFETIME_THRESHOLD`.

        The value is an integer expressing the age in years over which people are
        presumed to have died.
        """
        return self._lifetime_threshold

    @lifetime_threshold.setter
    def lifetime_threshold(self, lifetime_threshold: int) -> None:
        assert_positive_number()(lifetime_threshold)
        self._lifetime_threshold = lifetime_threshold
        self._dispatch_change()

    @override
    def update(self, other: Self) -> None:
        self._base_url = other._base_url
        self._title = other._title
        self._author = other._author
        self._root_path = other._root_path
        self._clean_urls = other._clean_urls
        self._debug = other._debug
        self._lifetime_threshold = other._lifetime_threshold
        self._locales.update(other._locales)
        self._extensions.update(other._extensions)
        self._entity_types.update(other._entity_types)
        self._dispatch_change()

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField("name", assert_str() | assert_setattr(self, "name")),
            RequiredField("base_url", assert_str() | assert_setattr(self, "base_url")),
            OptionalField("title", assert_str() | assert_setattr(self, "title")),
            OptionalField("author", assert_str() | assert_setattr(self, "author")),
            OptionalField(
                "root_path", assert_str() | assert_setattr(self, "root_path")
            ),
            OptionalField(
                "clean_urls",
                assert_bool() | assert_setattr(self, "clean_urls"),
            ),
            OptionalField("debug", assert_bool() | assert_setattr(self, "debug")),
            OptionalField(
                "lifetime_threshold",
                assert_int() | assert_setattr(self, "lifetime_threshold"),
            ),
            OptionalField("locales", self.locales.load),
            OptionalField("extensions", self.extensions.load),
            OptionalField("entity_types", self.entity_types.load),
        )(dump)

    @override
    def dump(self) -> VoidableDictDump[Dump]:
        return minimize(
            {  # type: ignore[return-value]
                "name": void_none(self.name),
                "base_url": self.base_url,
                "title": self.title,
                "root_path": void_none(self.root_path),
                "clean_urls": void_none(self.clean_urls),
                "author": void_none(self.author),
                "debug": void_none(self.debug),
                "lifetime_threshold": void_none(self.lifetime_threshold),
                "locales": self.locales.dump(),
                "extensions": self.extensions.dump(),
                "entity_types": self.entity_types.dump(),
            },
            True,
        )


class Project(Configurable[ProjectConfiguration], CoreComponent):
    """
    Define a Betty project.

    A project combines project configuration and the resulting ancestry.
    """

    def __init__(
        self,
        app: App,
        configuration: ProjectConfiguration,
        *,
        ancestry: Ancestry | None = None,
    ):
        super().__init__()
        self._app = app
        self._configuration = configuration
        self._ancestry = Ancestry() if ancestry is None else ancestry

        self._assets: AssetRepository | None = None
        self._localizers: LocalizerRepository | None = None
        self._url_generator: LocalizedUrlGenerator | None = None
        self._static_url_generator: StaticUrlGenerator | None = None
        self._jinja2_environment: Environment | None = None
        self._renderer: Renderer | None = None
        self._extensions: Extensions | None = None
        self._dispatcher: ExtensionDispatcher | None = None
        self._entity_types: set[type[Entity]] | None = None
        self._event_types: set[type[EventType]] | None = None

    @classmethod
    @asynccontextmanager
    async def new_temporary(
        cls, app: App, *, ancestry: Ancestry | None = None
    ) -> AsyncIterator[Self]:
        """
        Creat a new, temporary, isolated project.

        The project will not leave any traces on the system, except when it uses
        global Betty functionality such as caches.
        """
        async with (
            TemporaryDirectory() as project_directory_path_str,
        ):
            yield cls(
                app,
                ProjectConfiguration(Path(project_directory_path_str) / "betty.json"),
                ancestry=ancestry,
            )

    @property
    def app(self) -> App:
        """
        The application this project is run within.
        """
        return self._app

    @property
    def name(self) -> str:
        """
        The project name.

        If no project name was configured, this defaults to the hash of the configuration file path.
        """
        if self._configuration.name is None:
            return hashid(str(self._configuration.configuration_file_path))
        return self._configuration.name

    @property
    def ancestry(self) -> Ancestry:
        """
        The project's ancestry.
        """
        return self._ancestry

    @property
    def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        if self._assets is None:
            self._assert_bootstrapped()
            asset_paths = [self.configuration.assets_directory_path]
            for extension in self.extensions.flatten():
                extension_assets_directory_path = extension.assets_directory_path()
                if extension_assets_directory_path is not None:
                    asset_paths.append(extension_assets_directory_path)
            # Mimic :py:attr:`betty.app.App.assets`.
            asset_paths.append(fs.ASSETS_DIRECTORY_PATH)
            self._assets = AssetRepository(*asset_paths)
        return self._assets

    @property
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        if self._localizers is None:
            self._assert_bootstrapped()
            self._localizers = LocalizerRepository(self.assets)
        return self._localizers

    @property
    def url_generator(self) -> LocalizedUrlGenerator:
        """
        The (localized) URL generator.
        """
        if self._url_generator is None:
            from betty.url import ProjectUrlGenerator

            self._assert_bootstrapped()
            self._url_generator = ProjectUrlGenerator(self)
        return self._url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        """
        The static URL generator.
        """
        if self._static_url_generator is None:
            from betty.url import StaticPathUrlGenerator

            self._assert_bootstrapped()
            self._static_url_generator = StaticPathUrlGenerator(self.configuration)
        return self._static_url_generator

    @property
    def jinja2_environment(self) -> Environment:
        """
        The Jinja2 environment.
        """
        if not self._jinja2_environment:
            from betty.jinja2 import Environment

            self._assert_bootstrapped()
            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @property
    def renderer(self) -> Renderer:
        """
        The (file) content renderer.
        """
        if not self._renderer:
            from betty.jinja2 import Jinja2Renderer

            self._renderer = SequentialRenderer(
                [
                    Jinja2Renderer(self.jinja2_environment, self.configuration),
                ]
            )

        return self._renderer

    @property
    def extensions(self) -> Extensions:
        """
        The enabled extensions.
        """
        if self._extensions is None:
            extension_types_enabled_in_configuration = set()
            for (
                project_extension_configuration
            ) in self.configuration.extensions.values():
                if project_extension_configuration.enabled:
                    wait_to_thread(
                        project_extension_configuration.extension_type.enable_requirement().assert_met()
                    )
                    extension_types_enabled_in_configuration.add(
                        project_extension_configuration.extension_type
                    )

            extension_types_sorter = TopologicalSorter(
                build_extension_type_graph(extension_types_enabled_in_configuration)
            )
            try:
                extension_types_sorter.prepare()
            except CycleError:
                raise CyclicDependencyError(
                    [
                        app_extension_configuration.extension_type
                        for app_extension_configuration in self.configuration.extensions.values()
                    ]
                ) from None

            extensions = []
            while extension_types_sorter.is_active():
                extension_types_batch = extension_types_sorter.get_ready()
                extensions_batch = []
                for extension_type in extension_types_batch:
                    if (
                        issubclass(extension_type, ConfigurableExtension)
                        and extension_type in self.configuration.extensions
                    ):
                        extension: Extension = extension_type(
                            self,
                            configuration=self.configuration.extensions[
                                extension_type
                            ].extension_configuration,
                        )
                    else:
                        extension = extension_type(self)
                    extensions_batch.append(extension)
                    extension_types_sorter.done(extension_type)
                extensions.append(
                    sorted(extensions_batch, key=lambda extension: extension.name())
                )
            self._extensions = ListExtensions(extensions)

        return self._extensions

    def discover_extension_types(self) -> set[type[Extension]]:
        """
        Discover the available extension types.
        """
        from betty.project import extension

        return {
            *extension.discover_extension_types(),
            *map(type, self.extensions.flatten()),
        }

    @property
    def dispatcher(self) -> Dispatcher:
        """
        The event dispatcher.
        """
        if self._dispatcher is None:
            self._assert_bootstrapped()
            self._dispatcher = ExtensionDispatcher(self.extensions)

        return self._dispatcher

    @property
    def entity_types(self) -> set[type[Entity]]:
        """
        The available entity types.
        """
        if self._entity_types is None:
            self._assert_bootstrapped()
            from betty.model.ancestry import (
                Citation,
                Enclosure,
                Event,
                File,
                Note,
                Person,
                PersonName,
                Presence,
                Place,
                Source,
            )

            self._entity_types = reduce(
                operator.or_,
                wait_to_thread(self.dispatcher.dispatch(EntityTypeProvider)()),
                set(),
            ) | {
                Citation,
                Enclosure,
                Event,
                File,
                Note,
                Person,
                PersonName,
                Presence,
                Place,
                Source,
            }
        return self._entity_types

    @property
    def event_types(self) -> set[type[EventType]]:
        """
        The available event types.
        """
        if self._event_types is None:
            self._assert_bootstrapped()
            self._event_types = set(
                wait_to_thread(self.dispatcher.dispatch(EventTypeProvider)())
            ) | {
                Birth,
                Baptism,
                Adoption,
                Death,
                Funeral,
                Cremation,
                Burial,
                Will,
                Engagement,
                Marriage,
                MarriageAnnouncement,
                Divorce,
                DivorceAnnouncement,
                Residence,
                Immigration,
                Emigration,
                Occupation,
                Retirement,
                Correspondence,
                Confirmation,
            }
        return self._event_types
