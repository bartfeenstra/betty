from __future__ import annotations

from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type, List, Iterable, Dict, Any, Sequence
from urllib.parse import urlparse

from babel.core import parse_locale, Locale
from reactives import reactive, scope
from reactives.factory.type import ReactiveInstance

from betty.app import Extension, ConfigurableExtension
from betty.config import Configuration, DumpedConfiguration, ConfigurationError, minimize_dumped_configuration, \
    Configurable, FileBasedConfiguration
from betty.error import ensure_context
from betty.importlib import import_any
from betty.locale import bcp_47_to_rfc_1766
from betty.model import Entity, get_entity_type_name
from betty.model.ancestry import Ancestry, File
from betty.typing import Void

if TYPE_CHECKING:
    from betty.builtins import _


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

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if self._entity_type_constraint is None:
            if not isinstance(dumped_configuration, dict):
                raise ConfigurationError(_('The entity reference must be a mapping (dictionary).'))
            with ensure_context('entity_type'):
                if 'entity_type' not in dumped_configuration:
                    raise ConfigurationError(_('The entity type is required.'))
                try:
                    self._entity_type = import_any(dumped_configuration['entity_type'])
                except ImportError as e:
                    raise ConfigurationError(e)
            with ensure_context('entity_id'):
                if 'entity_id' not in dumped_configuration:
                    raise ConfigurationError(_('The entity ID is required.'))
                entity_id = dumped_configuration['entity_id']
        else:
            entity_id = dumped_configuration
        if not isinstance(entity_id, str):
            raise ConfigurationError(_('The entity ID must be a string.'))
        self._entity_id = entity_id
        self.react.trigger()

    def dump(self) -> DumpedConfiguration:
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

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(entity_type={self.entity_type}, entity_id={self._entity_id})'

    @scope.register_self
    def __eq__(self, other) -> bool:
        if not isinstance(other, EntityReference):
            return NotImplemented
        return self.entity_type == other.entity_type and self.entity_id == other.entity_id


class EntityReferences(Configuration):
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
                raise ConfigurationError(_('The entity reference must be for an entity of type {expected_entity_type_name} ({expected_entity_type_label}), but instead is for an entity of type {actual_entity_type_name} ({actual_entity_type_label})').format(
                    expected_entity_type_name=get_entity_type_name(self._entity_type_constraint),
                    expected_entity_type_label=self._entity_type_constraint.entity_type_label(),
                    actual_entity_type_name=get_entity_type_name(self._entity_type_constraint),
                    actual_entity_type_label=self._entity_type_constraint.entity_type_label(),
                ))
            entity_reference = EntityReference(None, entity_reference.entity_id, self._entity_type_constraint)
        self._entity_references.append(entity_reference)
        self.react.trigger()

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, list):
            raise ConfigurationError(_('Entity references must be a list.'))
        self._entity_references.clear()
        for i, dumped_entity_reference_configuration in enumerate(dumped_configuration):
            entity_reference = EntityReference(entity_type_constraint=self._entity_type_constraint)
            with ensure_context(str(i)):
                entity_reference.load(dumped_entity_reference_configuration)
            self._entity_references.append(entity_reference)
        self.react.trigger()

    def dump(self) -> DumpedConfiguration:
        return minimize_dumped_configuration([
            entity_reference.dump()
            for entity_reference
            in self._entity_references
        ])


@reactive
class ProjectExtensionConfiguration(ReactiveInstance):
    def __init__(self, extension_type: Type[Extension], enabled: bool = True, extension_configuration: Optional[Configuration] = None):
        super().__init__()
        self._extension_type = extension_type
        self._enabled = enabled
        if extension_configuration is None and issubclass(extension_type, ConfigurableExtension):
            extension_configuration = extension_type.default_configuration()
        if extension_configuration is not None:
            extension_configuration.react(self)
        self._extension_configuration = extension_configuration

    def __repr__(self):
        return '<%s.%s(%s)>' % (self.__class__.__module__, self.__class__.__name__, self.extension_type)

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


class ProjectExtensionsConfiguration(Configuration):
    def __init__(self, configurations: Optional[Iterable[ProjectExtensionConfiguration]] = None):
        super().__init__()
        self._configurations: Dict[Type[Extension], ProjectExtensionConfiguration] = OrderedDict()
        if configurations is not None:
            for configuration in configurations:
                self.add(configuration)

    def __contains__(self, item):
        return item in self._configurations

    @scope.register_self
    def __getitem__(self, extension_type: Type[Extension]) -> ProjectExtensionConfiguration:
        return self._configurations[extension_type]

    def __delitem__(self, extension_type: Type[Extension]) -> None:
        self.remove(extension_type)

    @scope.register_self
    def __iter__(self) -> Iterable[ProjectExtensionConfiguration]:
        return (configuration for configuration in self._configurations.values())

    @scope.register_self
    def __len__(self) -> int:
        return len(self._configurations)

    @scope.register_self
    def __eq__(self, other):
        if not isinstance(other, ProjectExtensionsConfiguration):
            return NotImplemented
        return self._configurations == other._configurations

    def remove(self, *extension_types: Type[Extension]) -> None:
        for extension_type in extension_types:
            with suppress(KeyError):
                self._configurations[extension_type].react.shutdown(self)
            del self._configurations[extension_type]
        self.react.trigger()

    def clear(self) -> None:
        self.remove(*self._configurations.keys())

    def add(self, *configurations: ProjectExtensionConfiguration) -> None:
        for configuration in configurations:
            self._configurations[configuration.extension_type] = configuration
            configuration.react(self)
        self.react.trigger()

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('App extensions configuration must be a mapping (dictionary).'))

        self.clear()

        for extension_type_name in dumped_configuration:
            with ensure_context(f'`{extension_type_name}`'):
                try:
                    extension_type = import_any(extension_type_name)
                except ImportError as e:
                    raise ConfigurationError(e)

                if not issubclass(extension_type, Extension):
                    raise ConfigurationError(_('"{extension_type_name}" is not a Betty extension.').format(extension_type_name=extension_type_name))

                dumped_extension_configuration = dumped_configuration[extension_type_name]

                if not isinstance(dumped_extension_configuration, dict):
                    raise ConfigurationError(_('The configuration must be a mapping (dictionary).'))

                if 'enabled' in dumped_extension_configuration:
                    if not isinstance(dumped_extension_configuration['enabled'], bool):
                        raise ConfigurationError(
                            'The extension must be declared enabled (true) or disabled (false).',
                            contexts=['`enabled`'],
                        )
                    enabled = dumped_extension_configuration['enabled']
                else:
                    enabled = True

                if 'configuration' in dumped_extension_configuration:
                    if not issubclass(extension_type, ConfigurableExtension):
                        raise ConfigurationError(f'{extension_type_name} is not configurable.', contexts=['`configuration`'])
                    extension_configuration = extension_type.default_configuration()
                    extension_configuration.load(dumped_extension_configuration['configuration'])
                else:
                    extension_configuration = None

                self.add(ProjectExtensionConfiguration(
                    extension_type,
                    enabled,
                    extension_configuration,
                ))

    def dump(self) -> DumpedConfiguration:
        dumped_configuration: Any = {}
        for app_extension_configuration in self:
            extension_type = app_extension_configuration.extension_type
            dumped_configuration[extension_type.name()] = {
                'enabled': app_extension_configuration.enabled,
            }
            if issubclass(extension_type, Configurable):
                dumped_app_extension_configuration = app_extension_configuration.extension_configuration.dump()
                if dumped_app_extension_configuration is not Void:
                    dumped_configuration[extension_type.name()]['configuration'] = dumped_app_extension_configuration
            dumped_configuration[extension_type.name()] = minimize_dumped_configuration(dumped_configuration[extension_type.name()])
        return minimize_dumped_configuration(dumped_configuration)


class LocaleConfiguration:
    def __init__(self, locale: str, alias: Optional[str] = None):
        self._locale = locale
        if alias is not None and '/' in alias:
            raise ConfigurationError(_('Locale aliases must not contain slashes.'))
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


class LocalesConfiguration(Configuration):
    def __init__(self, configurations: Optional[Sequence[LocaleConfiguration]] = None):
        super().__init__()
        self._configurations: OrderedDict[str, LocaleConfiguration] = OrderedDict()
        self.replace(configurations)

    @scope.register_self
    def __getitem__(self, locale: str) -> LocaleConfiguration:
        return self._configurations[locale]

    def __delitem__(self, locale: str) -> None:
        if len(self._configurations) <= 1:
            raise ConfigurationError(_('Cannot remove the last remaining locale {locale}').format(locale=Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name()))
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
        if not isinstance(other, LocalesConfiguration):
            return NotImplemented
        return self._configurations == other._configurations

    @scope.register_self
    def __contains__(self, item):
        return item in self._configurations

    @scope.register_self
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, repr(list(self._configurations.values())))

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

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, list):
            raise ConfigurationError(_('Locales configuration must be a list.'))

        if len(dumped_configuration) > 0:
            self._configurations.clear()
            for dumped_locale_configuration in dumped_configuration:
                locale = dumped_locale_configuration['locale']
                try:
                    parse_locale(bcp_47_to_rfc_1766(locale))
                except ValueError:
                    raise ConfigurationError(_('{locale} is not a valid IETF BCP 47 language tag.').format(locale=locale))
                self.add(LocaleConfiguration(
                    locale,
                    dumped_locale_configuration['alias'] if 'alias' in dumped_locale_configuration else None,
                ))

    def dump(self) -> DumpedConfiguration:
        dumped_configuration = []
        for locale_configuration in self:
            dumped_locale_configuration = {
                'locale': locale_configuration.locale,
            }
            if locale_configuration.alias != locale_configuration.locale:
                dumped_locale_configuration['alias'] = locale_configuration.alias
            dumped_configuration.append(dumped_locale_configuration)
        return dumped_configuration


class ThemeConfiguration(Configuration):
    def __init__(self):
        super().__init__()
        self._background_image = EntityReference(entity_type_constraint=File)
        self._featured_entities = EntityReferences()
        self._featured_entities.react(self)

    @reactive  # type: ignore
    @property
    def background_image(self) -> EntityReference:
        return self._background_image

    @property
    def featured_entities(self) -> EntityReferences:
        return self._featured_entities

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('The theme configuration must be a mapping (dictionary).'))

        if 'background_image_id' in dumped_configuration:
            with ensure_context('background_image_id'):
                self.background_image.load(dumped_configuration['background_image_id'])

        if 'featured_entities' in dumped_configuration:
            with ensure_context('featured_entities'):
                self.featured_entities.load(dumped_configuration['featured_entities'])

    def dump(self) -> DumpedConfiguration:
        return minimize_dumped_configuration({
            'background_image_id': self._background_image.dump(),
            'featured_entities': self.featured_entities.dump(),
        })


class ProjectConfiguration(FileBasedConfiguration):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__()
        self._base_url = 'https://example.com' if base_url is None else base_url
        self._root_path = ''
        self._clean_urls = False
        self._content_negotiation = False
        self._title = 'Betty'
        self._author: Optional[str] = None
        self._extensions = ProjectExtensionsConfiguration()
        self._extensions.react(self)
        self._debug = False
        self._locales = LocalesConfiguration()
        self._locales.react(self)
        self._theme = ThemeConfiguration()
        self._theme.react(self)
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
    def base_url(self, base_url: str):
        base_url_parts = urlparse(base_url)
        if not base_url_parts.scheme:
            raise ConfigurationError(_('The base URL must start with a scheme such as https://, http://, or file://.'))
        if not base_url_parts.netloc:
            raise ConfigurationError(_('The base URL must include a path.'))
        self._base_url = '%s://%s' % (base_url_parts.scheme, base_url_parts.netloc)

    @reactive  # type: ignore
    @property
    def root_path(self) -> str:
        return self._root_path

    @root_path.setter
    def root_path(self, root_path: str):
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
    def clean_urls(self, clean_urls: bool):
        self._clean_urls = clean_urls

    @reactive  # type: ignore
    @property
    def locales(self) -> LocalesConfiguration:
        return self._locales

    @property
    def multilingual(self) -> bool:
        return len(self.locales) > 1

    @property
    def extensions(self) -> ProjectExtensionsConfiguration:
        return self._extensions

    @reactive  # type: ignore
    @property
    def theme(self) -> ThemeConfiguration:
        return self._theme

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
    def lifetime_threshold(self, lifetime_threshold: int):
        if lifetime_threshold < 1:
            raise ConfigurationError(_('The lifetime threshold must be a positive number.'))
        self._lifetime_threshold = lifetime_threshold

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('Betty project configuration must be a mapping (dictionary).'))

        if 'base_url' not in dumped_configuration or not isinstance(dumped_configuration['base_url'], str):
            raise ConfigurationError(_('The base URL is required and must be a string.'), contexts=['`base_url`'])
        self.base_url = dumped_configuration['base_url']

        if 'title' in dumped_configuration:
            if not isinstance(dumped_configuration['title'], str):
                raise ConfigurationError(_('The title must be a string.'), contexts=['`title`'])
            self.title = dumped_configuration['title']

        if 'author' in dumped_configuration:
            if not isinstance(dumped_configuration['author'], str):
                raise ConfigurationError(_('The author must be a string.'), contexts=['`author`'])
            self.author = dumped_configuration['author']

        if 'root_path' in dumped_configuration:
            if not isinstance(dumped_configuration['root_path'], str):
                raise ConfigurationError(_('The root path must be a string.'), contexts=['`root_path`'])
            self.root_path = dumped_configuration['root_path']

        if 'clean_urls' in dumped_configuration:
            if not isinstance(dumped_configuration['clean_urls'], bool):
                raise ConfigurationError(_('Clean URLs must be enabled (true) or disabled (false) with a boolean.'), contexts=['`clean_urls`'])
            self.clean_urls = dumped_configuration['clean_urls']

        if 'content_negotiation' in dumped_configuration:
            if not isinstance(dumped_configuration['content_negotiation'], bool):
                raise ConfigurationError(_('Content negotiation must be enabled (true) or disabled (false) with a boolean.'), contexts=['`content_negotiation`'])
            self.content_negotiation = dumped_configuration['content_negotiation']

        if 'debug' in dumped_configuration:
            if not isinstance(dumped_configuration['debug'], bool):
                raise ConfigurationError(_('Debugging must be enabled (true) or disabled (false) with a boolean.'), contexts=['`debug`'])
            self.debug = dumped_configuration['debug']

        if 'lifetime_threshold' in dumped_configuration:
            if not isinstance(dumped_configuration['lifetime_threshold'], int):
                raise ConfigurationError(_('The lifetime threshold must be an integer.'), contexts=['`lifetime_threshold`'])
            self.lifetime_threshold = dumped_configuration['lifetime_threshold']

        if 'locales' in dumped_configuration:
            with ensure_context('`locales`'):
                self._locales.load(dumped_configuration['locales'])

        if 'extensions' in dumped_configuration:
            with ensure_context('`extensions`'):
                self._extensions.load(dumped_configuration['extensions'])

        if 'theme' in dumped_configuration:
            with ensure_context('`theme`'):
                self._theme.load(dumped_configuration['theme'])

    def dump(self) -> DumpedConfiguration:
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
        if self.lifetime_threshold is not None:
            dumped_configuration['lifetime_threshold'] = self.lifetime_threshold
        dumped_configuration['theme'] = self.theme.dump()

        return minimize_dumped_configuration(dumped_configuration)


class Project(Configurable[ProjectConfiguration]):
    def __init__(self):
        super().__init__()
        self._configuration = ProjectConfiguration()
        self._ancestry = Ancestry()

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry
