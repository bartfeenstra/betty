from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Person, Place, LocalizedName, PersonName
from betty.config import Configuration, LocaleConfiguration
from betty.plugins.search import index, Search
from betty.site import Site


class IndexTest(TestCase):
    def test_person_without_names(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            configuration.plugins[Search] = {}
            site = Site(configuration)
            person_id = 'P1'
            person = Person(person_id)
            site.ancestry.people[person_id] = person
            expected = []
            self.assertEquals(expected, list(index(site)))

    def test_person_with_individual_name(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            configuration.plugins[Search] = {}
            site = Site(configuration)
            person_id = 'P1'
            individual_name = 'Jane'
            person = Person(person_id)
            person.names.append(PersonName(individual_name))
            site.ancestry.people[person_id] = person
            expected = [
                {
                    'text': 'jane',
                    'results': {
                        'nl-NL': '\n<a href="/nl/person/P1/index.html" class="nav-secondary-action search-result-target">Jane</a>',
                        'en-US': '\n<a href="/en/person/P1/index.html" class="nav-secondary-action search-result-target">Jane</a>',
                    },
                },
            ]
            self.assertEquals(expected, list(index(site)))

    def test_person_with_affiliation_name(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            configuration.plugins[Search] = {}
            site = Site(configuration)
            person_id = 'P1'
            affiliation_name = 'Doughnut'
            person = Person(person_id)
            person.names.append(PersonName(None, affiliation_name))
            site.ancestry.people[person_id] = person
            expected = [
                {
                    'text': 'doughnut',
                    'results': {
                        'nl-NL': '\n<a href="/nl/person/P1/index.html" class="nav-secondary-action search-result-target">… Doughnut</a>',
                        'en-US': '\n<a href="/en/person/P1/index.html" class="nav-secondary-action search-result-target">… Doughnut</a>',
                    },
                },
            ]
            self.assertEquals(expected, list(index(site)))

    def test_person_with_individual_and_affiliation_names(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            configuration.plugins[Search] = {}
            site = Site(configuration)
            person_id = 'P1'
            individual_name = 'Jane'
            affiliation_name = 'Doughnut'
            person = Person(person_id)
            person.names.append(PersonName(individual_name, affiliation_name))
            site.ancestry.people[person_id] = person
            expected = [
                {
                    'text': 'jane doughnut',
                    'results': {
                        'nl-NL': '\n<a href="/nl/person/P1/index.html" class="nav-secondary-action search-result-target">Jane Doughnut</a>',
                        'en-US': '\n<a href="/en/person/P1/index.html" class="nav-secondary-action search-result-target">Jane Doughnut</a>',
                    },
                },
            ]
            self.assertEquals(expected, list(index(site)))

    def test_place(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            configuration.plugins[Search] = {}
            site = Site(configuration)
            place_id = 'P1'
            place = Place(place_id, [LocalizedName(
                'Netherlands', 'en'), LocalizedName('Nederland', 'nl')])
            site.ancestry.places[place_id] = place
            expected = [
                {
                    'text': 'netherlands nederland',
                    'results': {
                        'nl-NL': '\n<a href="/nl/place/P1/index.html" class="nav-secondary-action search-result-target">Nederland</a>',
                        'en-US': '\n<a href="/en/place/P1/index.html" class="nav-secondary-action search-result-target">Netherlands</a>',
                    },
                },
            ]
            self.assertEquals(expected, list(index(site)))

    def test_empty(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            configuration.plugins[Search] = {}
            site = Site(configuration)
            expected = []
            self.assertEquals(expected, list(index(site)))
