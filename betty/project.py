from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from reprlib import recursive_repr
from typing import Any, Generic, final, Iterable, cast, Self
from urllib.parse import urlparse

from reactives import scope
from reactives.instance.property import reactive_property

from betty.app.extension import Extension, ConfigurableExtension
from betty.classtools import repr_instance
from betty.config import Configuration, Configurable, FileBasedConfiguration, ConfigurationMapping, \
    ConfigurationSequence
from betty.locale import get_data, Str
from betty.model import Entity, get_entity_type_name, UserFacingEntity, EntityT
from betty.model.ancestry import Ancestry, Person, Event, Place, Source
from betty.serde.dump import Dump, VoidableDump, void_none, minimize, Void, VoidableDictDump
from betty.serde.load import AssertionFailed, Fields, Assertions, Assertion, RequiredField, OptionalField, \
    Asserter

DEFAULT_LIFETIME_THRESHOLD = 125


class EntityReference(Configuration, Generic[EntityT]):
    def __init__(
        self,
        entity_type: type[EntityT] | None = None,
        entity_id: str | None = None,
        *,
        entity_type_is_constrained: bool = False,
    ):
        super().__init__()
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._entity_type_is_constrained = entity_type_is_constrained

    @property
    @reactive_property
    def entity_type(self) -> type[EntityT] | None:
        return self._entity_type

    @entity_type.setter
    def entity_type(self, entity_type: type[EntityT]) -> None:
        if self._entity_type_is_constrained:
            raise AttributeError(f'The entity type cannot be set, as it is already constrained to {self._entity_type}.')
        self._entity_type = entity_type

    @property
    @reactive_property
    def entity_id(self) -> str | None:
        return self._entity_id

    @entity_id.setter
    def entity_id(self, entity_id: str) -> None:
        self._entity_id = entity_id

    @entity_id.deleter
    def entity_id(self) -> None:
        self._entity_id = None

    @property
    def entity_type_is_constrained(self) -> bool:
        return self._entity_type_is_constrained

    def update(self, other: Self) -> None:
        self._entity_type = other._entity_type
        self._entity_type_is_constrained = other._entity_type_is_constrained
        self._entity_id = other._entity_id
        self.react.trigger()

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        if isinstance(dump, dict) or not configuration.entity_type_is_constrained:
            asserter.assert_record(Fields(
                RequiredField(
                    'entity_type',
                    Assertions(asserter.assert_entity_type()) | asserter.assert_setattr(configuration, 'entity_type'),
                ),
                OptionalField(
                    'entity_id',
                    Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'entity_id'),
                ),
            ))(dump)
        else:
            asserter.assert_str()(dump)
            asserter.assert_setattr(configuration, 'entity_id')(dump)  # type: ignore[arg-type]
        return configuration

    def dump(self) -> VoidableDump:
        if self.entity_type_is_constrained:
            return void_none(self.entity_id)

        if self.entity_type is None or self.entity_id is None:
            return Void

        dump: VoidableDictDump[VoidableDump] = {
            'entity_type': get_entity_type_name(self._entity_type) if self._entity_type else Void,
            'entity_id': self._entity_id,
        }

        return minimize(dump)

    @scope.register_self
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EntityReference):
            return NotImplemented
        return self.entity_type == other.entity_type and self.entity_id == other.entity_id


class EntityReferenceSequence(Generic[EntityT], ConfigurationSequence[EntityReference[EntityT]]):
    def __init__(
        self,
        entity_references: Iterable[EntityReference[EntityT]] | None = None,
        *,
        entity_type_constraint: type[EntityT] | None = None,
    ):
        self._entity_type_constraint = entity_type_constraint
        super().__init__(entity_references)

    @classmethod
    def _item_type(cls) -> type[EntityReference[EntityT]]:
        return EntityReference

    def _on_add(self, configuration: EntityReference[EntityT]) -> None:
        super()._on_add(configuration)

        entity_type_constraint = self._entity_type_constraint
        entity_reference_entity_type = configuration._entity_type

        if entity_type_constraint is None:
            return

        if entity_reference_entity_type == entity_type_constraint and configuration.entity_type_is_constrained:
            return

        expected_entity_type_name = get_entity_type_name(
            cast(type[Entity], entity_type_constraint),
        )
        expected_entity_type_label = entity_type_constraint.entity_type_label()

        if entity_reference_entity_type is None:
            raise AssertionFailed(Str._(
                'The entity reference must be for an entity of type {expected_entity_type_name} ({expected_entity_type_label}), but instead does not specify an entity type at all.',
                expected_entity_type_name=expected_entity_type_name,
                expected_entity_type_label=expected_entity_type_label,
            ))

        actual_entity_type_label = entity_type_constraint.entity_type_label()

        raise AssertionFailed(Str._(
            'The entity reference must be for an entity of type {expected_entity_type_name} ({expected_entity_type_label}), but instead is for an entity of type {actual_entity_type_name} ({actual_entity_type_label})',
            expected_entity_type_name=expected_entity_type_name,
            expected_entity_type_label=expected_entity_type_label,
            actual_entity_type_name=get_entity_type_name(entity_reference_entity_type),
            actual_entity_type_label=actual_entity_type_label,
        ))


class ExtensionConfiguration(Configuration):
    def __init__(
        self,
        extension_type: type[Extension],
        enabled: bool = True,
        extension_configuration: Configuration | None = None,
    ):
        super().__init__()
        self._extension_type = extension_type
        self._enabled = enabled
        if extension_configuration is None and issubclass(extension_type, ConfigurableExtension):
            extension_configuration = extension_type.default_configuration()
        if extension_configuration is not None:
            extension_configuration.react(self)
        self._extension_configuration = extension_configuration

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
        return self._extension_type

    @property
    @reactive_property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def extension_configuration(self) -> Configuration | None:
        return self._extension_configuration

    def update(self, other: Self) -> None:
        raise NotImplementedError(repr(self))

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        asserter = Asserter()
        extension_type = asserter.assert_field(RequiredField(
            'extension',
            Assertions(asserter.assert_extension_type()),
        ))(dump)
        if configuration is None:
            configuration = cls(extension_type)
        else:
            # This MUST NOT fail. If it does, this is a bug in the calling code that must be fixed.
            assert extension_type is configuration.extension_type
        asserter.assert_record(Fields(
            RequiredField(
                'extension',
            ),
            OptionalField(
                'enabled',
                Assertions(asserter.assert_bool()) | asserter.assert_setattr(configuration, 'enabled'),
            ),
            OptionalField(
                'configuration',
                Assertions(configuration._assert_load_extension_configuration(configuration.extension_type)),
            ),
        ))(dump)
        return configuration

    def _assert_load_extension_configuration(self, extension_type: type[Extension]) -> Assertion[Any, Configuration]:
        def _assertion(value: Any) -> Configuration:
            extension_configuration = self._extension_configuration
            if isinstance(extension_configuration, Configuration):
                return extension_configuration.load(value, extension_configuration)
            raise AssertionFailed(Str._(
                '{extension_type} is not configurable.',
                extension_type=extension_type.name(),
            ))
        return _assertion

    def dump(self) -> VoidableDump:
        return minimize({
            'extension': self.extension_type.name(),
            'enabled': self.enabled,
            'configuration': minimize(self.extension_configuration.dump()) if issubclass(self.extension_type, Configurable) and self.extension_configuration else Void,
        })


class ExtensionConfigurationMapping(ConfigurationMapping[type[Extension], ExtensionConfiguration]):
    def _minimize_item_dump(self) -> bool:
        return True

    @classmethod
    def _create_default_item(cls, configuration_key: type[Extension]) -> ExtensionConfiguration:
        return ExtensionConfiguration(configuration_key)

    def __init__(
        self,
        configurations: Iterable[ExtensionConfiguration] | None = None,
    ):
        super().__init__(configurations)

    @classmethod
    def _item_type(cls) -> type[ExtensionConfiguration]:
        return ExtensionConfiguration

    def _get_key(self, configuration: ExtensionConfiguration) -> type[Extension]:
        return configuration.extension_type

    @classmethod
    def _load_key(
        cls,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        asserter = Asserter()
        dict_dump = asserter.assert_dict()(item_dump)
        dict_dump['extension'] = key_dump
        return dict_dump

    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dict_dump = self._asserter.assert_dict()(item_dump)
        return dict_dump, dict_dump.pop('extension')

    def enable(self, *extension_types: type[Extension]) -> None:
        for extension_type in extension_types:
            try:
                self._configurations[extension_type].enabled = True
            except KeyError:
                self.append(ExtensionConfiguration(extension_type, True))

    def disable(self, *extension_types: type[Extension]) -> None:
        for extension_type in extension_types:
            with suppress(KeyError):
                self._configurations[extension_type].enabled = False


class EntityTypeConfiguration(Configuration):
    def __init__(self, entity_type: type[Entity], generate_html_list: bool | None = None):
        super().__init__()
        self._entity_type = entity_type
        self.generate_html_list = generate_html_list  # type: ignore[assignment]

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
        return self._entity_type

    @property
    @reactive_property
    def generate_html_list(self) -> bool:
        return self._generate_html_list or False

    @generate_html_list.setter
    def generate_html_list(self, generate_html_list: bool | None) -> None:
        if generate_html_list and not issubclass(self._entity_type, UserFacingEntity):
            raise AssertionFailed(Str._(
                'Cannot generate pages for {entity_type}, because it is not a user-facing entity type.',
                entity_type=get_entity_type_name(self._entity_type)
            ))
        self._generate_html_list = generate_html_list

    def update(self, other: Self) -> None:
        self._entity_type = other._entity_type
        self._generate_html_list = other._generate_html_list
        self.react.trigger()

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
    ) -> Self:
        asserter = Asserter()
        entity_type = asserter.assert_field(RequiredField[Any, type[Entity]](
            'entity_type',
            Assertions(asserter.assert_str()) | asserter.assert_entity_type()),
        )(dump)
        configuration = cls(entity_type)
        asserter.assert_record(Fields(
            OptionalField(
                'entity_type',
            ),
            OptionalField(
                'generate_html_list',
                Assertions(asserter.assert_bool()) | asserter.assert_setattr(configuration, 'generate_html_list'),
            ),
        ))(dump)
        return configuration

    def dump(self) -> VoidableDump:
        dump: VoidableDictDump[VoidableDump] = {
            'entity_type': get_entity_type_name(self._entity_type),
            'generate_html_list': Void if self._generate_html_list is None else self._generate_html_list,
        }

        return minimize(dump)


class EntityTypeConfigurationMapping(ConfigurationMapping[type[Entity], EntityTypeConfiguration]):
    def _minimize_item_dump(self) -> bool:
        return True

    def _get_key(self, configuration: EntityTypeConfiguration) -> type[Entity]:
        return configuration.entity_type

    @classmethod
    def _load_key(
        cls,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        asserter = Asserter()
        dict_dump = asserter.assert_dict()(item_dump)
        asserter.assert_entity_type()(key_dump)
        dict_dump['entity_type'] = key_dump
        return dict_dump

    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dict_dump = self._asserter.assert_dict()(item_dump)
        return dict_dump, dict_dump.pop('entity_type')

    @classmethod
    def _item_type(cls) -> type[EntityTypeConfiguration]:
        return EntityTypeConfiguration

    @classmethod
    def _create_default_item(cls, configuration_key: type[Entity]) -> EntityTypeConfiguration:
        return EntityTypeConfiguration(configuration_key)


class LocaleConfiguration(Configuration):
    def __init__(self, locale: str, alias: str | None = None):
        super().__init__()
        self._locale = locale
        if alias is not None and '/' in alias:
            raise AssertionFailed(Str._('Locale aliases must not contain slashes.'))
        self._alias = alias

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, locale=self.locale, alias=self.alias)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.locale != other.locale:
            return False
        if self.alias != other.alias:
            return False
        return True

    def __hash__(self) -> int:
        return hash((self._locale, self._alias))

    @property
    def locale(self) -> str:
        return self._locale

    @property
    @reactive_property
    def alias(self) -> str:
        if self._alias is None:
            return self.locale
        return self._alias

    @alias.setter
    def alias(self, alias: str | None) -> None:
        self._alias = alias

    def update(self, other: Self) -> None:
        self._locale = other._locale
        self._alias = other._alias

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
    ) -> Self:
        asserter = Asserter()
        locale = asserter.assert_field(RequiredField(
            'locale',
            Assertions(asserter.assert_locale())),
        )(dump)
        if configuration is None:
            configuration = cls(locale)
        asserter.assert_record(Fields(
            RequiredField(
                'locale'
            ),
            OptionalField(
                'alias',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'alias'),
            ),
        ))(dump)
        return configuration

    def dump(self) -> VoidableDump:
        return minimize({
            'locale': self.locale,
            'alias': void_none(self._alias)
        })


class LocaleConfigurationMapping(ConfigurationMapping[str, LocaleConfiguration]):
    @classmethod
    def _create_default_item(cls, configuration_key: str) -> LocaleConfiguration:
        return LocaleConfiguration(configuration_key)

    def __init__(
        self,
        configurations: Iterable[LocaleConfiguration] | None = None,
    ):
        super().__init__(configurations)
        if len(self) == 0:
            self.append(LocaleConfiguration('en-US'))

    def _get_key(self, configuration: LocaleConfiguration) -> str:
        return configuration.locale

    @classmethod
    def _load_key(
        cls,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        asserter = Asserter()
        dict_item_dump = asserter.assert_dict()(item_dump)
        dict_item_dump['locale'] = key_dump
        return dict_item_dump

    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dict_item_dump = self._asserter.assert_dict()(item_dump)
        return dict_item_dump, dict_item_dump.pop('locale')

    @classmethod
    def _item_type(cls) -> type[LocaleConfiguration]:
        return LocaleConfiguration

    def _on_remove(self, configuration: LocaleConfiguration) -> None:
        if len(self._configurations) <= 1:
            raise AssertionFailed(Str._(
                'Cannot remove the last remaining locale {locale}',
                locale=get_data(configuration.locale).get_display_name() or configuration.locale,
            ))

    @property
    @reactive_property
    def default(self) -> LocaleConfiguration:
        return next(iter(self._configurations.values()))

    @default.setter
    def default(self, configuration: LocaleConfiguration | str) -> None:
        if isinstance(configuration, str):
            configuration = self[configuration]
        self._configurations[configuration.locale] = configuration
        self._configurations.move_to_end(configuration.locale, False)
        self.react.trigger()

    @property
    def multilingual(self) -> bool:
        return len(self) > 1


@final
class ProjectConfiguration(FileBasedConfiguration):
    def __init__(self, base_url: str | None = None):
        super().__init__()
        self._base_url = 'https://example.com' if base_url is None else base_url
        self._root_path = ''
        self._clean_urls = False
        self._content_negotiation = False
        self._title = 'Betty'
        self._author: str | None = None
        self._entity_types = EntityTypeConfigurationMapping([
            EntityTypeConfiguration(Person, True),
            EntityTypeConfiguration(Event, True),
            EntityTypeConfiguration(Place, True),
            EntityTypeConfiguration(Source, True),
        ])
        self._entity_types.react(self)
        self._extensions = ExtensionConfigurationMapping()
        self._extensions.react(self)
        self._debug = False
        self._locales = LocaleConfigurationMapping()
        self._locales.react(self)
        self._lifetime_threshold = DEFAULT_LIFETIME_THRESHOLD

    @property
    def project_directory_path(self) -> Path:
        return self.configuration_file_path.parent

    @property
    def output_directory_path(self) -> Path:
        return self.project_directory_path / 'output'

    @property
    def assets_directory_path(self) -> Path:
        return self.project_directory_path / 'assets'

    @property
    def www_directory_path(self) -> Path:
        return self.output_directory_path / 'www'

    def localize_www_directory_path(self, locale: str) -> Path:
        if self.locales.multilingual:
            return self.www_directory_path / self.locales[locale].alias
        return self.www_directory_path

    @property
    @reactive_property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @property
    @reactive_property
    def author(self) -> str | None:
        return self._author

    @author.setter
    def author(self, author: str | None) -> None:
        self._author = author

    @property
    @reactive_property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, base_url: str) -> None:
        base_url_parts = urlparse(base_url)
        if not base_url_parts.scheme:
            raise AssertionFailed(Str._('The base URL must start with a scheme such as https://, http://, or file://.'))
        if not base_url_parts.netloc:
            raise AssertionFailed(Str._('The base URL must include a path.'))
        self._base_url = '%s://%s' % (base_url_parts.scheme, base_url_parts.netloc)

    @property
    @reactive_property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, root_path: str) -> None:
        self._root_path = root_path.strip('/')

    @property
    @reactive_property
    def content_negotiation(self) -> bool:
        return self._content_negotiation

    @content_negotiation.setter
    def content_negotiation(self, content_negotiation: bool) -> None:
        self._content_negotiation = content_negotiation

    @property
    @reactive_property
    def clean_urls(self) -> bool:
        return self._clean_urls or self.content_negotiation

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool) -> None:
        self._clean_urls = clean_urls

    @property
    def locales(self) -> LocaleConfigurationMapping:
        return self._locales

    @property
    def entity_types(self) -> EntityTypeConfigurationMapping:
        return self._entity_types

    @property
    def extensions(self) -> ExtensionConfigurationMapping:
        return self._extensions

    @property
    @reactive_property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._debug = debug

    @property
    @reactive_property
    def lifetime_threshold(self) -> int:
        return self._lifetime_threshold

    @lifetime_threshold.setter
    def lifetime_threshold(self, lifetime_threshold: int) -> None:
        self._asserter.assert_positive_number()(lifetime_threshold)
        self._lifetime_threshold = lifetime_threshold

    def update(self, other: Self) -> None:
        self._base_url = other._base_url
        self._title = other._title
        self._author = other._author
        self._root_path = other._root_path
        self._clean_urls = other._clean_urls
        self._content_negotiation = other._content_negotiation
        self._debug = other._debug
        self._lifetime_threshold = other._lifetime_threshold
        self._locales.update(other._locales)
        self._extensions.update(other._extensions)
        self._entity_types.update(other._entity_types)

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(Fields(
            RequiredField(
                'base_url',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'base_url'),
            ),
            OptionalField(
                'title',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'title'),
            ),
            OptionalField(
                'author',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'author'),
            ),
            OptionalField(
                'root_path',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'root_path'),
            ),
            OptionalField(
                'clean_urls',
                Assertions(asserter.assert_bool()) | asserter.assert_setattr(configuration, 'clean_urls'),
            ),
            OptionalField(
                'content_negotiation',
                Assertions(asserter.assert_bool()) | asserter.assert_setattr(configuration, 'content_negotiation'),
            ),
            OptionalField(
                'debug',
                Assertions(asserter.assert_bool()) | asserter.assert_setattr(configuration, 'debug'),
            ),
            OptionalField(
                'lifetime_threshold',
                Assertions(asserter.assert_int()) | asserter.assert_setattr(configuration, 'lifetime_threshold'),
            ),
            OptionalField(
                'locales',
                Assertions(configuration._locales.assert_load(configuration.locales)),
            ),
            OptionalField(
                'extensions',
                Assertions(configuration._extensions.assert_load(configuration.extensions)),
            ),
            OptionalField(
                'entity_types',
                Assertions(configuration._entity_types.assert_load(configuration.entity_types)),
            ),
        ))(dump)
        return configuration

    def dump(self) -> VoidableDictDump[Dump]:
        return minimize({  # type: ignore[return-value]
            'base_url': self.base_url,
            'title': self.title,
            'root_path': void_none(self.root_path),
            'clean_urls': void_none(self.clean_urls),
            'author': void_none(self.author),
            'content_negotiation': void_none(self.content_negotiation),
            'debug': void_none(self.debug),
            'lifetime_threshold': void_none(self.lifetime_threshold),
            'locales': self.locales.dump(),
            'extensions': self.extensions.dump(),
            'entity_types': self.entity_types.dump(),
        }, True)


class Project(Configurable[ProjectConfiguration]):
    def __init__(self):
        super().__init__()
        self._configuration = ProjectConfiguration()
        self._ancestry = Ancestry()

    def __getstate__(self) -> tuple[VoidableDump, Path, Ancestry]:
        return self._configuration.dump(), self._configuration.configuration_file_path, self._ancestry

    def __setstate__(self, state: tuple[Dump, Path, Ancestry]) -> None:
        dump, configuration_file_path, self._ancestry = state
        self._configuration = ProjectConfiguration.load(dump)
        self._configuration.configuration_file_path = configuration_file_path

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry
