from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Optional, Type, Any, Generic, final, Tuple, Iterable
from urllib.parse import urlparse
from reactives import scope
from reactives.instance.property import reactive_property

from betty.app import Extension, ConfigurableExtension
from betty.config import Configuration, DumpedConfiguration, Configurable, FileBasedConfiguration, \
    ConfigurationMapping, VoidableDumpedConfiguration, ConfigurationSequence
from betty.config.dump import minimize, void_none
from betty.config.load import ConfigurationValidationError, assert_str, assert_record, Fields, Assertions, \
    assert_entity_type, assert_setattr, assert_field, assert_extension_type, assert_bool, Assertion, assert_dict, \
    assert_locale, assert_positive_number, assert_int, RequiredField, OptionalField
from betty.locale import Localizer, Localizable, get_data
from betty.model import Entity, get_entity_type_name, UserFacingEntity, EntityT
from betty.model.ancestry import Ancestry, Person, Event, Place, Source
from betty.typing import Void

try:
    from typing_extensions import Self
except ModuleNotFoundError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover


class EntityReference(Configuration, Generic[EntityT]):
    def __init__(
            self,
            entity_type: Type[EntityT] | None = None,
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
    def entity_type(self) -> Type[EntityT] | None:
        return self._entity_type

    @entity_type.setter
    def entity_type(self, entity_type: Type[EntityT] | None) -> None:
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
    def load(cls, dumped_configuration: DumpedConfiguration, configuration: Self | None = None) -> Self:
        if configuration is None:
            configuration = cls()
        if isinstance(dumped_configuration, dict):
            assert_record(Fields(
                RequiredField(
                    'entity_type',
                    Assertions(assert_entity_type()) | assert_setattr(configuration, 'entity_type'),
                ),
                OptionalField(
                    'entity_id',
                    Assertions(assert_str()) | assert_setattr(configuration, 'entity_id'),
                ),
            ))(dumped_configuration)
        else:
            assert_str()(dumped_configuration)
            assert_setattr(configuration, 'entity_id')(dumped_configuration)  # type: ignore[arg-type]
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        if self.entity_type_is_constrained:
            return void_none(self.entity_id)

        if self.entity_type is None or self.entity_id is None:
            return Void

        return minimize({
            'entity_type': get_entity_type_name(self._entity_type) if self._entity_type else Void,
            'entity_id': self._entity_id,
        })

    @scope.register_self
    def __eq__(self, other) -> bool:
        if not isinstance(other, EntityReference):
            return NotImplemented
        return self.entity_type == other.entity_type and self.entity_id == other.entity_id


class EntityReferenceSequence(ConfigurationSequence[EntityReference]):
    def __init__(
        self,
        entity_references: Iterable[EntityReference] | None = None,
        *,
        entity_type_constraint: Type[Entity] | None = None,
        localizer: Localizer | None = None,
    ):
        self._entity_type_constraint = entity_type_constraint
        super().__init__(entity_references, localizer=localizer)

    @classmethod
    def _item_type(cls) -> Type[EntityReference]:
        return EntityReference

    def _on_add(self, entity_reference: EntityReference) -> None:
        super()._on_add(entity_reference)
        if self._entity_type_constraint:
            if entity_reference.entity_type != self._entity_type_constraint or not entity_reference.entity_type_is_constrained:
                raise ConfigurationValidationError(self.localizer._('The entity reference must be for an entity of type {expected_entity_type_name} ({expected_entity_type_label}), but instead is for an entity of type {actual_entity_type_name} ({actual_entity_type_label})').format(
                    expected_entity_type_name=get_entity_type_name(self._entity_type_constraint),
                    expected_entity_type_label=self._entity_type_constraint.entity_type_label(localizer=self.localizer) if issubclass(self._entity_type_constraint, UserFacingEntity) else get_entity_type_name(self._entity_type_constraint),
                    actual_entity_type_name=get_entity_type_name(self._entity_type_constraint),
                    actual_entity_type_label=self._entity_type_constraint.entity_type_label(localizer=self.localizer) if issubclass(self._entity_type_constraint, UserFacingEntity) else get_entity_type_name(self._entity_type_constraint),
                ))


class ExtensionConfiguration(Configuration):
    def __init__(self, extension_type: Type[Extension], enabled: bool = True, extension_configuration: Optional[Configuration] = None, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._extension_type = extension_type
        self._enabled = enabled
        if extension_configuration is None and issubclass(extension_type, ConfigurableExtension):
            extension_configuration = extension_type.default_configuration()
        if extension_configuration is not None:
            extension_configuration.react(self)
        self._extension_configuration = extension_configuration

    def __eq__(self, other):
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
    def extension_type(self) -> Type[Extension]:
        return self._extension_type

    @property
    @reactive_property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def extension_configuration(self) -> Optional[Configuration]:
        return self._extension_configuration

    def update(self, other: Self) -> None:
        raise NotImplementedError

    @classmethod
    def load(cls, dumped_configuration: DumpedConfiguration, configuration: Self | None = None) -> Self:
        extension_type = assert_field(RequiredField(
            'extension',
            Assertions(assert_extension_type()),
        ))(dumped_configuration)
        assert extension_type is not Void
        if configuration is None:
            configuration = cls(extension_type)  # type: ignore[arg-type]
        else:
            # This MUST NOT fail. If it does, this is a bug in the calling code that must be fixed.
            assert extension_type is configuration.extension_type
        assert_record(Fields(
            RequiredField(
                'extension',
            ),
            OptionalField(
                'enabled',
                Assertions(assert_bool()) | assert_setattr(configuration, 'enabled'),
            ),
            OptionalField(
                'configuration',
                Assertions(configuration._assert_load_extension_configuration(configuration.extension_type)),
            ),
        ))(dumped_configuration)
        return configuration

    def _assert_load_extension_configuration(self, extension_type: Type[Extension]) -> Assertion[Any, Configuration]:
        def _assertion(value: Any) -> Configuration:
            extension_configuration = self._extension_configuration
            if isinstance(extension_configuration, Configuration):
                return extension_configuration.load(value, extension_configuration)
            raise ConfigurationValidationError(self.localizer._('{extension_type} is not configurable.').format(
                extension_type=extension_type.name(),
            ))
        return _assertion

    def dump(self) -> VoidableDumpedConfiguration:
        return minimize({
            'extension': self.extension_type.name(),
            'enabled': self.enabled,
            'configuration': minimize(self.extension_configuration.dump()) if issubclass(self.extension_type, Configurable) and self.extension_configuration else Void,
        })


class ExtensionConfigurationMapping(ConfigurationMapping[Type[Extension], ExtensionConfiguration]):
    def _minimize_dumped_item_configuration(self) -> bool:
        return True

    @classmethod
    def _create_default_item(cls, configuration_key: Type[Extension]) -> ExtensionConfiguration:
        return ExtensionConfiguration(configuration_key)

    def __init__(
        self,
        configurations: Iterable[ExtensionConfiguration] | None = None,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(configurations, localizer=localizer)

    @classmethod
    def _item_type(cls) -> Type[ExtensionConfiguration]:
        return ExtensionConfiguration

    def _get_key(self, configuration: ExtensionConfiguration) -> Type[Extension]:
        return configuration.extension_type

    @classmethod
    def _load_key(cls, dumped_item: DumpedConfiguration, dumped_key: str) -> DumpedConfiguration:
        dumped_item_dict = assert_dict()(dumped_item)
        dumped_item_dict['extension'] = dumped_key
        return dumped_item_dict

    def _dump_key(self, dumped_item: VoidableDumpedConfiguration) -> Tuple[VoidableDumpedConfiguration, str]:
        dumped_item_dict = assert_dict()(dumped_item)
        return dumped_item_dict, dumped_item_dict.pop('extension')

    def enable(self, *extension_types: Type[Extension]):
        for extension_type in extension_types:
            try:
                self._configurations[extension_type].enabled = True
            except KeyError:
                self.append(ExtensionConfiguration(extension_type, True))

    def disable(self, *extension_types: Type[Extension]):
        for extension_type in extension_types:
            with suppress(KeyError):
                self._configurations[extension_type].enabled = False


class EntityTypeConfiguration(Configuration):
    def __init__(self, entity_type: Type[Entity], generate_html_list: Optional[bool] = None):
        super().__init__()
        self._entity_type = entity_type
        self.generate_html_list = generate_html_list  # type: ignore[assignment]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.entity_type != other.entity_type:
            return False
        if self.generate_html_list != other.generate_html_list:
            return False
        return True

    @property
    def entity_type(self) -> Type[Entity]:
        return self._entity_type

    @property
    @reactive_property
    def generate_html_list(self) -> bool:
        return self._generate_html_list or False

    @generate_html_list.setter
    def generate_html_list(self, generate_html_list: Optional[bool]) -> None:
        if generate_html_list and not issubclass(self._entity_type, UserFacingEntity):
            raise ConfigurationValidationError(self.localizer._('Cannot generate pages for {entity_type}, because it is not a user-facing entity type.').format(
                entity_type=get_entity_type_name(self._entity_type)
            ))
        self._generate_html_list = generate_html_list

    def update(self, other: Self) -> None:
        self._entity_type = other._entity_type
        self._generate_html_list = other._generate_html_list
        self.react.trigger()

    @classmethod
    def load(cls, dumped_configuration: DumpedConfiguration, template: Self | None = None) -> Self:
        entity_type = assert_field(RequiredField[Any, Type[Entity]]('entity_type', Assertions(assert_str()) | assert_entity_type()))(dumped_configuration)
        configuration = cls(entity_type)
        assert_record(Fields(
            OptionalField('entity_type'),
            OptionalField('generate_html_list', Assertions(assert_bool()) | assert_setattr(configuration, 'generate_html_list')),
        ))(dumped_configuration)
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        return minimize({
            'entity_type': get_entity_type_name(self._entity_type),
            'generate_html_list': Void if self._generate_html_list is None else self._generate_html_list,
        })


class EntityTypeConfigurationMapping(ConfigurationMapping[Type[Entity], EntityTypeConfiguration]):
    def _minimize_dumped_item_configuration(self) -> bool:
        return True

    def _get_key(self, configuration: EntityTypeConfiguration) -> Type[Entity]:
        return configuration.entity_type

    @classmethod
    def _load_key(cls, dumped_item: DumpedConfiguration, dumped_key: str) -> DumpedConfiguration:
        dumped_item_dict = assert_dict()(dumped_item)
        assert_entity_type()(dumped_key)
        dumped_item_dict['entity_type'] = dumped_key
        return dumped_item_dict

    def _dump_key(self, dumped_item: VoidableDumpedConfiguration) -> Tuple[VoidableDumpedConfiguration, str]:
        dumped_item_dict = assert_dict()(dumped_item)
        return dumped_item_dict, dumped_item_dict.pop('entity_type')

    @classmethod
    def _item_type(cls) -> Type[EntityTypeConfiguration]:
        return EntityTypeConfiguration

    @classmethod
    def _create_default_item(cls, entity_type: Type[Entity]) -> EntityTypeConfiguration:
        return EntityTypeConfiguration(entity_type)


class LocaleConfiguration(Configuration):
    def __init__(self, locale: str, alias: str | None = None, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._locale = locale
        if alias is not None and '/' in alias:
            raise ConfigurationValidationError(self.localizer._('Locale aliases must not contain slashes.'))
        self._alias = alias

    def __repr__(self):
        return '<%s.%s(%s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.locale, self.alias)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.locale != other.locale:
            return False
        if self.alias != other.alias:
            return False
        return True

    def __hash__(self):
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
    def alias(self, alias: Optional[str]) -> None:
        self._alias = alias

    def update(self, other: Self) -> None:
        self._locale = other._locale
        self._alias = other._alias

    @classmethod
    def load(cls, dumped_configuration: DumpedConfiguration, configuration: Self | None = None) -> Self:
        locale = assert_field(RequiredField('locale', Assertions(assert_locale())))(dumped_configuration)
        if configuration is None:
            configuration = cls(locale)
        assert_record(Fields(
            RequiredField('locale'),
            OptionalField('alias', Assertions(assert_str()) | assert_setattr(configuration, 'alias')),
        ))(dumped_configuration)
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
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
        *,
        localizer: Localizer | None = None
    ):
        super().__init__(configurations, localizer=localizer)
        if len(self) == 0:
            self.append(LocaleConfiguration('en-US'))

    def _get_key(self, configuration: LocaleConfiguration) -> str:
        return configuration.locale

    @classmethod
    def _load_key(cls, dumped_item: DumpedConfiguration, dumped_key: str) -> DumpedConfiguration:
        dumped_item_dict = assert_dict()(dumped_item)
        dumped_item_dict['locale'] = dumped_key
        return dumped_item_dict

    def _dump_key(self, dumped_item: VoidableDumpedConfiguration) -> Tuple[VoidableDumpedConfiguration, str]:
        dumped_item_dict = assert_dict()(dumped_item)
        return dumped_item_dict, dumped_item_dict.pop('locale')

    @classmethod
    def _item_type(cls) -> Type[LocaleConfiguration]:
        return LocaleConfiguration

    def _on_remove(self, locale: LocaleConfiguration) -> None:
        if len(self._configurations) <= 1:
            raise ConfigurationValidationError(self.localizer._('Cannot remove the last remaining locale {locale}').format(
                locale=get_data(locale.locale).get_display_name()),
            )

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


@final
class ProjectConfiguration(FileBasedConfiguration):
    def __init__(self, base_url: Optional[str] = None, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._base_url = 'https://example.com' if base_url is None else base_url
        self._root_path = ''
        self._clean_urls = False
        self._content_negotiation = False
        self._title = 'Betty'
        self._author: Optional[str] = None
        self._entity_types = EntityTypeConfigurationMapping([
            EntityTypeConfiguration(Person, True),
            EntityTypeConfiguration(Event, True),
            EntityTypeConfiguration(Place, True),
            EntityTypeConfiguration(Source, True),
        ], localizer=self._localizer)
        self._entity_types.react(self)
        self._extensions = ExtensionConfigurationMapping(localizer=self._localizer)
        self._extensions.react(self)
        self._debug = False
        self._locales = LocaleConfigurationMapping(localizer=self._localizer)
        self._locales.react(self)
        self._lifetime_threshold = 125

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

    @property
    @reactive_property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @property
    @reactive_property
    def author(self) -> Optional[str]:
        return self._author

    @author.setter
    def author(self, author: Optional[str]) -> None:
        self._author = author

    @property
    @reactive_property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, base_url: str) -> None:
        base_url_parts = urlparse(base_url)
        if not base_url_parts.scheme:
            raise ConfigurationValidationError(self.localizer._('The base URL must start with a scheme such as https://, http://, or file://.'))
        if not base_url_parts.netloc:
            raise ConfigurationValidationError(self.localizer._('The base URL must include a path.'))
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
    def content_negotiation(self, content_negotiation: bool):
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
    def multilingual(self) -> bool:
        return len(self.locales) > 1

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
        assert_positive_number()(lifetime_threshold)
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
    def load(cls, dumped_configuration: DumpedConfiguration, configuration: Self | None = None) -> Self:
        if configuration is None:
            configuration = cls()
        assert_record(Fields(
            RequiredField('base_url', Assertions(assert_str()) | assert_setattr(configuration, 'base_url')),
            OptionalField('title', Assertions(assert_str()) | assert_setattr(configuration, 'title')),
            OptionalField('author', Assertions(assert_str()) | assert_setattr(configuration, 'author')),
            OptionalField('root_path', Assertions(assert_str()) | assert_setattr(configuration, 'root_path')),
            OptionalField('clean_urls', Assertions(assert_bool()) | assert_setattr(configuration, 'clean_urls')),
            OptionalField('content_negotiation', Assertions(assert_bool()) | assert_setattr(configuration, 'content_negotiation')),
            OptionalField('debug', Assertions(assert_bool()) | assert_setattr(configuration, 'debug')),
            OptionalField('lifetime_threshold', Assertions(assert_int()) | assert_setattr(configuration, 'lifetime_threshold')),
            OptionalField('locales', Assertions(configuration._locales.assert_load(configuration.locales))),
            OptionalField('extensions', Assertions(configuration._extensions.assert_load(configuration.extensions))),
            OptionalField('entity_types', Assertions(configuration._entity_types.assert_load(configuration.entity_types))),
        ))(dumped_configuration)
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        return minimize({
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


class Project(Configurable[ProjectConfiguration], Localizable):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._configuration = ProjectConfiguration(localizer=localizer)
        self._ancestry = Ancestry()

    def __getstate__(self) -> Tuple[VoidableDumpedConfiguration, Path, Ancestry]:
        return self._configuration.dump(), self._configuration.configuration_file_path, self._ancestry

    def __setstate__(self, state: Tuple[DumpedConfiguration, Path, Ancestry]) -> None:
        dumped_configuration, configuration_file_path, self._ancestry = state
        self._configuration = ProjectConfiguration.load(dumped_configuration)
        self._configuration.configuration_file_path = configuration_file_path

    def _on_localizer_change(self) -> None:
        self._configuration.localizer = self.localizer
        self._ancestry.localizer = self.localizer

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry
