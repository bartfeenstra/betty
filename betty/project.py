from __future__ import annotations

from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type, List, Iterable, Any, Sequence, cast
from urllib.parse import urlparse

from babel.core import parse_locale, Locale
from reactives import reactive, scope

from betty.app import Extension, ConfigurableExtension
from betty.classtools import repr_instance
from betty.config import Configuration, DumpedConfigurationImport, Configurable, FileBasedConfiguration, \
    ConfigurationMapping, DumpedConfigurationExport, DumpedConfigurationDict
from betty.config.dump import minimize, minimize_dict
from betty.config.load import ConfigurationValidationError, Loader, Field
from betty.config.validate import validate, validate_positive_number
from betty.importlib import import_any
from betty.locale import bcp_47_to_rfc_1766
from betty.model import Entity, get_entity_type_name, UserFacingEntity, get_entity_type as model_get_entity_type, \
    EntityTypeImportError, EntityTypeInvalidError, EntityTypeError
from betty.model.ancestry import Ancestry, Person, Event, Place, Source
from betty.typing import Void

try:
    from typing_extensions import TypeGuard
except ModuleNotFoundError:  # pragma: no cover
    from typing import TypeGuard  # type: ignore  # pragma: no cover

if TYPE_CHECKING:
    from betty.builtins import _


def get_entity_type(entity_type_definition: Any) -> Type[Entity]:
    try:
        return model_get_entity_type(entity_type_definition)
    except EntityTypeImportError:
        raise ConfigurationValidationError(_('Cannot find and import "{entity_type}".').format(
            entity_type=str(entity_type_definition),
        ))
    except EntityTypeInvalidError:
        raise ConfigurationValidationError(_('"{entity_type}" is not a valid Betty entity type.').format(
            entity_type=str(entity_type_definition),
        ))
    except EntityTypeError:
        raise ConfigurationValidationError(_('Cannot determine the entity type for "{entity_type}". Did you perhaps make a typo, or could it be that the entity type comes from another package that is not yet installed?').format(
            entity_type=str(entity_type_definition),
        ))


class EntityReference(Configuration):
    def __init__(self, entity_type: Optional[Type[Entity]] = None, entity_id: Optional[str] = None, /, entity_type_constraint: Optional[Type[Entity]] = None):
        super().__init__()
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._entity_type_constraint = entity_type_constraint

    @reactive  # type: ignore
    @property
    def entity_type(self) -> Optional[Type[Entity]]:
        return self._entity_type or self._entity_type_constraint

    @entity_type.setter
    def entity_type(self, entity_type: Type[Entity]) -> None:
        if self._entity_type_constraint is not None:
            raise AttributeError(f'The entity type cannot be set, as it is already constrained to {self._entity_type_constraint}.')
        self._entity_type = entity_type

    @reactive  # type: ignore
    @property
    def entity_id(self) -> Optional[str]:
        return self._entity_id

    @entity_id.setter
    def entity_id(self, entity_id: str) -> None:
        self._entity_id = entity_id

    @entity_id.deleter
    def entity_id(self) -> None:
        self._entity_id = None

    @property
    def entity_type_constraint(self) -> Optional[Type[Entity]]:
        return self._entity_type_constraint

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        if self._entity_type_constraint is None:
            loader.assert_record(dumped_configuration, {
                'entity_type': Field(
                    True,
                    self._load_entity_type,  # type: ignore
                ),
                'entity_id': Field(
                    True,
                    loader.assert_str,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'entity_id', x),
                ),
            })
        elif loader.assert_str(dumped_configuration):
            loader.assert_setattr(self, 'entity_id', dumped_configuration)

    def _load_entity_type(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> TypeGuard[str]:
        with loader.context() as errors:
            if loader.assert_str(dumped_configuration):
                with loader.catch():
                    loader.assert_setattr(self, 'entity_type', get_entity_type(dumped_configuration))
        return errors.valid

    def dump(self) -> DumpedConfigurationExport:
        if self._entity_id is None:
            return Void
        if self._entity_type_constraint is None:
            if self._entity_type is None:
                return Void
            return {
                'entity_type': get_entity_type_name(self._entity_type),
                'entity_id': self._entity_id,
            }
        return self._entity_id

    @scope.register_self
    def __eq__(self, other) -> bool:
        if not isinstance(other, EntityReference):
            return NotImplemented
        return self.entity_type == other.entity_type and self.entity_id == other.entity_id


class EntityReferenceCollection(Configuration):
    def __init__(self, entity_references: Optional[List[EntityReference]] = None, /, entity_type_constraint: Optional[Type[Entity]] = None):
        super().__init__()
        self._entity_type_constraint = entity_type_constraint
        self._entity_references = entity_references or []

    @scope.register_self
    def __iter__(self):
        return (reference for reference in self._entity_references)

    @scope.register_self
    def __len__(self) -> int:
        return len(self._entity_references)

    @property
    def entity_type_constraint(self) -> Optional[Type[Entity]]:
        return self._entity_type_constraint

    def __getitem__(self, key):
        return self._entity_references[key]

    def __delitem__(self, key):
        del self._entity_references[key]

    def append(self, entity_reference: EntityReference) -> None:
        if self._entity_type_constraint:
            if entity_reference.entity_type != self._entity_type_constraint:
                raise ConfigurationValidationError(_('The entity reference must be for an entity of type {expected_entity_type_name} ({expected_entity_type_label}), but instead is for an entity of type {actual_entity_type_name} ({actual_entity_type_label})').format(
                    expected_entity_type_name=get_entity_type_name(self._entity_type_constraint),
                    expected_entity_type_label=self._entity_type_constraint.entity_type_label() if issubclass(self._entity_type_constraint, UserFacingEntity) else get_entity_type_name(self._entity_type_constraint),
                    actual_entity_type_name=get_entity_type_name(self._entity_type_constraint),
                    actual_entity_type_label=self._entity_type_constraint.entity_type_label() if issubclass(self._entity_type_constraint, UserFacingEntity) else get_entity_type_name(self._entity_type_constraint),
                ))
            entity_reference = EntityReference(None, entity_reference.entity_id, self._entity_type_constraint)
        self._entity_references.append(entity_reference)
        self.react.trigger()

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        if loader.assert_list(dumped_configuration):
            loader.on_commit(self._entity_references.clear)
            loader.assert_sequence(
                dumped_configuration,
                self._load_entity_reference,  # type: ignore
            )

    def _load_entity_reference(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> TypeGuard[DumpedConfigurationDict[DumpedConfigurationImport]]:
        with loader.context() as errors:
            entity_reference = EntityReference(entity_type_constraint=self._entity_type_constraint)
            entity_reference.load(dumped_configuration, loader)
            loader.on_commit(lambda: self._entity_references.append(entity_reference))
        return errors.valid

    def dump(self) -> DumpedConfigurationExport:
        return minimize([
            entity_reference.dump()
            for entity_reference
            in self._entity_references
        ])


class ExtensionConfiguration(Configuration):
    def __init__(self, extension_type: Type[Extension], enabled: bool = True, extension_configuration: Optional[Configuration] = None):
        super().__init__()
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

    @reactive  # type: ignore
    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def extension_configuration(self) -> Optional[Configuration]:
        return self._extension_configuration

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'enabled': Field(
                False,
                loader.assert_bool,  # type: ignore
                lambda x: loader.assert_setattr(self, 'enabled', x),
            ),
            'configuration': Field(
                False,
                self._load_extension_configuration,  # type: ignore
            ),
        })

    def _load_extension_configuration(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> TypeGuard[DumpedConfigurationDict[DumpedConfigurationImport]]:
        extension_type = self.extension_type
        if issubclass(extension_type, ConfigurableExtension):
            cast(ExtensionConfiguration, self.extension_configuration).load(dumped_configuration, loader)
            return True
        loader.error(ConfigurationValidationError(_('{extension_type} is not configurable.').format(
            extension_type=extension_type.name(),
        )))
        return False

    def dump(self) -> DumpedConfigurationExport:
        return minimize_dict({
            'enabled': self.enabled,
            'configuration': self.extension_configuration.dump() if issubclass(self.extension_type, Configurable) and self.extension_configuration else Void,
        }, True)


class ExtensionConfigurationMapping(ConfigurationMapping[Type[Extension], ExtensionConfiguration]):
    def _get_key(self, configuration: ExtensionConfiguration) -> Type[Extension]:
        return configuration.extension_type

    def _load_key(self, dumped_configuration_key: str) -> Type[Extension]:
        try:
            return import_any(dumped_configuration_key)
        except ImportError:
            raise ConfigurationValidationError(_('{extension_type} is not a valid Betty extension.').format(
                extension_type=dumped_configuration_key,
            ))

    def _dump_key(self, configuration_key: Type[Extension]) -> str:
        return configuration_key.name()

    def _default_configuration_item(self, configuration_key: Type[Extension]) -> ExtensionConfiguration:
        return ExtensionConfiguration(configuration_key)

    def enable(self, *extension_types: Type[Extension]):
        for extension_type in extension_types:
            try:
                self._configurations[extension_type].enabled = True
            except KeyError:
                self.add(self._default_configuration_item(extension_type))

    def disable(self, *extension_types: Type[Extension]):
        for extension_type in extension_types:
            with suppress(KeyError):
                self._configurations[extension_type].enabled = False


class EntityTypeConfiguration(Configuration):
    def __init__(self, entity_type: Type[Entity], generate_html_list: Optional[bool] = None):
        super().__init__()
        self._entity_type = entity_type
        self.generate_html_list = generate_html_list

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

    @reactive  # type: ignore
    @property
    def generate_html_list(self) -> bool:
        return self._generate_html_list or False

    @generate_html_list.setter
    def generate_html_list(self, generate_html_list: Optional[bool]) -> None:
        if not issubclass(self._entity_type, UserFacingEntity):
            raise ValueError(f'Cannot generate HTML pages for entity types that do not inherit from {UserFacingEntity.__module__}.{UserFacingEntity.__name__}.')
        self._generate_html_list = generate_html_list

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'generate_html_list': Field(
                False,
                loader.assert_bool,  # type: ignore
                lambda x: loader.assert_setattr(self, 'generate_html_list', x),
            ),
        })

    def dump(self) -> DumpedConfigurationExport:
        return minimize_dict({
            'generate_html_list': Void if self._generate_html_list is None else self._generate_html_list,
        }, True)


class EntityTypeConfigurationMapping(ConfigurationMapping[Type[Entity], EntityTypeConfiguration]):
    def _get_key(self, configuration: EntityTypeConfiguration) -> Type[Entity]:
        return configuration.entity_type

    def _load_key(self, dumped_configuration_key: str) -> Type[Entity]:
        return get_entity_type(dumped_configuration_key)

    def _dump_key(self, configuration_key: Type[Entity]) -> str:
        return get_entity_type_name(configuration_key)

    def _default_configuration_item(self, configuration_key: Type[Entity]) -> EntityTypeConfiguration:
        return EntityTypeConfiguration(configuration_key)


class LocaleConfiguration:
    def __init__(self, locale: str, alias: Optional[str] = None):
        self._locale = locale
        if alias is not None and '/' in alias:
            raise ConfigurationValidationError(_('Locale aliases must not contain slashes.'))
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
    def alias(self) -> str:
        if self._alias is None:
            return self.locale
        return self._alias


class LocaleConfigurationCollection(Configuration):
    def __init__(self, configurations: Optional[Sequence[LocaleConfiguration]] = None):
        super().__init__()
        self._configurations: OrderedDict[str, LocaleConfiguration] = OrderedDict()
        self.replace(configurations)

    @scope.register_self
    def __getitem__(self, locale: str) -> LocaleConfiguration:
        return self._configurations[locale]

    def __delitem__(self, locale: str) -> None:
        if len(self._configurations) <= 1:
            raise ConfigurationValidationError(_('Cannot remove the last remaining locale {locale}').format(locale=Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name()))
        del self._configurations[locale]
        self.react.trigger()

    @scope.register_self
    def __iter__(self) -> Iterable[LocaleConfiguration]:
        return (configuration for configuration in self._configurations.values())

    @scope.register_self
    def __len__(self) -> int:
        return len(self._configurations)

    @scope.register_self
    def __eq__(self, other):
        if not isinstance(other, LocaleConfigurationCollection):
            return NotImplemented
        return self._configurations == other._configurations

    @scope.register_self
    def __contains__(self, item):
        return item in self._configurations

    @scope.register_self
    def __repr__(self):
        return repr_instance(self, configurations=list(self._configurations.values()))

    def add(self, configuration: LocaleConfiguration) -> None:
        self._configurations[configuration.locale] = configuration
        self.react.trigger()

    def replace(self, configurations: Optional[Sequence[LocaleConfiguration]] = None) -> None:
        self._configurations.clear()
        if configurations is None or len(configurations) < 1:
            configurations = [LocaleConfiguration('en-US')]
        for configuration in configurations:
            self._configurations[configuration.locale] = configuration
        self.react.trigger()

    @reactive  # type: ignore
    @property
    def default(self) -> LocaleConfiguration:
        return next(iter(self._configurations.values()))

    @default.setter
    def default(self, configuration: LocaleConfiguration) -> None:
        self._configurations[configuration.locale] = configuration
        self._configurations.move_to_end(configuration.locale, False)
        self.react.trigger()

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.on_commit(self._configurations.clear)
        loader.assert_sequence(
            dumped_configuration,
            self._load_locale,  # type: ignore
        )

    def _load_locale(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> TypeGuard[DumpedConfigurationDict[DumpedConfigurationImport]]:
        if loader.assert_dict(dumped_configuration):
            with loader.assert_required_key(
                dumped_configuration,
                'locale',
                loader.assert_str,  # type: ignore
            ) as (dumped_locale, valid):
                if valid:
                    try:
                        parse_locale(
                            bcp_47_to_rfc_1766(
                                dumped_locale,  # type: ignore
                            ),
                        )
                    except ValueError:
                        loader.error(ConfigurationValidationError(_('{locale} is not a valid IETF BCP 47 language tag.').format(locale=dumped_locale)))
                    else:
                        loader.on_commit(lambda: self.add(LocaleConfiguration(
                            dumped_locale,  # type: ignore
                            dumped_configuration['alias'] if 'alias' in dumped_configuration else None,  # type: ignore
                        )))
                        return True
        return False

    def dump(self) -> DumpedConfigurationExport:
        dumped_configuration = []
        for locale_configuration in self:
            dumped_locale_configuration = {
                'locale': locale_configuration.locale,
            }
            if locale_configuration.alias != locale_configuration.locale:
                dumped_locale_configuration['alias'] = locale_configuration.alias
            dumped_configuration.append(dumped_locale_configuration)
        return dumped_configuration


class ProjectConfiguration(FileBasedConfiguration):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__()
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
        ])
        self._entity_types.react(self)
        self._extensions = ExtensionConfigurationMapping()
        self._extensions.react(self)
        self._debug = False
        self._locales = LocaleConfigurationCollection()
        self._locales.react(self)
        self._lifetime_threshold = 125

    @property
    def project_directory_path(self) -> Path:
        return self.configuration_file_path.parent

    @reactive  # type: ignore
    @property
    def output_directory_path(self) -> Path:
        return self.project_directory_path / 'output'

    @reactive  # type: ignore
    @property
    def assets_directory_path(self) -> Path:
        return self.project_directory_path / 'assets'

    @property
    def www_directory_path(self) -> Path:
        return self.output_directory_path / 'www'

    @reactive  # type: ignore
    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @reactive  # type: ignore
    @property
    def author(self) -> Optional[str]:
        return self._author

    @author.setter
    def author(self, author: Optional[str]) -> None:
        self._author = author

    @reactive  # type: ignore
    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, base_url: str) -> None:
        base_url_parts = urlparse(base_url)
        if not base_url_parts.scheme:
            raise ConfigurationValidationError(_('The base URL must start with a scheme such as https://, http://, or file://.'))
        if not base_url_parts.netloc:
            raise ConfigurationValidationError(_('The base URL must include a path.'))
        self._base_url = '%s://%s' % (base_url_parts.scheme, base_url_parts.netloc)

    @reactive  # type: ignore
    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, root_path: str) -> None:
        self._root_path = root_path.strip('/')

    @reactive  # type: ignore
    @property
    def content_negotiation(self) -> bool:
        return self._content_negotiation

    @content_negotiation.setter
    def content_negotiation(self, content_negotiation: bool):
        self._content_negotiation = content_negotiation

    @reactive  # type: ignore
    @property
    def clean_urls(self) -> bool:
        return self._clean_urls or self.content_negotiation

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool) -> None:
        self._clean_urls = clean_urls

    @reactive  # type: ignore
    @property
    def locales(self) -> LocaleConfigurationCollection:
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

    @reactive  # type: ignore
    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._debug = debug

    @reactive  # type: ignore
    @property
    def lifetime_threshold(self) -> int:
        return self._lifetime_threshold

    @lifetime_threshold.setter
    @validate(validate_positive_number)
    def lifetime_threshold(self, lifetime_threshold: int) -> None:
        self._lifetime_threshold = lifetime_threshold

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.assert_record(
            dumped_configuration,
            {
                'base_url': Field(
                    True,
                    loader.assert_str,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'base_url', x),
                ),
                'title': Field(
                    False,
                    loader.assert_str,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'title', x),
                ),
                'author': Field(
                    False,
                    loader.assert_str,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'author', x),
                ),
                'root_path': Field(
                    False,
                    loader.assert_str,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'root_path', x),
                ),
                'clean_urls': Field(
                    False,
                    loader.assert_bool,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'clean_urls', x),
                ),
                'content_negotiation': Field(
                    False,
                    loader.assert_bool,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'content_negotiation', x),
                ),
                'debug': Field(
                    False,
                    loader.assert_bool,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'debug', x),
                ),
                'lifetime_threshold': Field(
                    False,
                    loader.assert_int,  # type: ignore
                    lambda x: loader.assert_setattr(self, 'lifetime_threshold', x),
                ),
                'locales': Field(
                    False,
                    self._locales.load,  # type: ignore
                ),
                'extensions': Field(
                    False,
                    self._extensions.load,  # type: ignore
                ),
                'entity_types': Field(
                    False,
                    self._entity_types.load,  # type: ignore
                ),
            },
        )

    def dump(self) -> DumpedConfigurationExport:
        dumped_configuration = {
            'base_url': self.base_url,
            'title': self.title,
        }
        if self.root_path is not None:
            dumped_configuration['root_path'] = self.root_path
        if self.clean_urls is not None:
            dumped_configuration['clean_urls'] = self.clean_urls
        if self.author is not None:
            dumped_configuration['author'] = self.author
        if self.content_negotiation is not None:
            dumped_configuration['content_negotiation'] = self.content_negotiation
        if self.debug is not None:
            dumped_configuration['debug'] = self.debug
        dumped_configuration['locales'] = self.locales.dump()
        dumped_configuration['extensions'] = self.extensions.dump()
        dumped_configuration['entity_types'] = self.entity_types.dump()
        if self.lifetime_threshold is not None:
            dumped_configuration['lifetime_threshold'] = self.lifetime_threshold

        return minimize(dumped_configuration)


class Project(Configurable[ProjectConfiguration]):
    def __init__(self):
        super().__init__()
        self._configuration = ProjectConfiguration()
        self._ancestry = Ancestry()

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry
