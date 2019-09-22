from typing import Any, Callable

from betty.ancestry import Person, Citation, Source, File, Place, Event
from betty.config import Configuration
from betty.locale import Locale


class UrlGenerator:
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, target: Any, absolute: bool = False, locale: Locale = None) -> str:
        if locale is None:
            locale = self._configuration.default_locale
        _GENERATORS = {
            str: self._generate_for_path,
            Person: self._generator_for_identifiable('person/%s/'),
            Event: self._generator_for_identifiable('event/%s/'),
            Place: self._generator_for_identifiable('place/%s/'),
            File: self._generator_for_identifiable('file/%s/'),
            Source: self._generator_for_identifiable('source/%s/'),
            Citation: self._generator_for_identifiable('citation/%s/'),
        }
        generator = _GENERATORS[type(target)]
        return generator(target, absolute, locale)

    def _generator_for_identifiable(self, pattern: str) -> Callable:
        return lambda identifiable, absolute, locale: self._generate_for_path(pattern % identifiable.id, absolute, locale)

    def _generate_for_path(self, path: str, absolute: bool = False, locale: Locale = None):
        url = self._configuration.base_url if absolute else ''
        url += self._configuration.root_path
        if path.endswith('/'):
            if self._configuration.multilingual:
                url += locale.get_identifier() + '/'
        url += path.lstrip('/')
        if path.endswith('/') and not self._configuration.clean_urls:
            url += 'index.html'
        return url
