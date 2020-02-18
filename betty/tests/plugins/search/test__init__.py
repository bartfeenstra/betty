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

            indexed = list(index(site))

            self.assertEquals([], indexed)

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

            indexed = list(index(site))

            self.assertEquals('jane', indexed[0]['text'])
            self.assertIn('/nl/person/P1/index.html', indexed[0]['results']['nl-NL'])
            self.assertIn('/en/person/P1/index.html', indexed[0]['results']['en-US'])

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

            indexed = list(index(site))

            self.assertEquals('doughnut', indexed[0]['text'])
            self.assertIn('/nl/person/P1/index.html', indexed[0]['results']['nl-NL'])
            self.assertIn('/en/person/P1/index.html', indexed[0]['results']['en-US'])

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

            indexed = list(index(site))

            self.assertEquals('jane doughnut', indexed[0]['text'])
            self.assertIn('/nl/person/P1/index.html', indexed[0]['results']['nl-NL'])
            self.assertIn('/en/person/P1/index.html', indexed[0]['results']['en-US'])

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

            indexed = list(index(site))

            self.assertEquals('netherlands nederland', indexed[0]['text'])
            self.assertIn('/nl/place/P1/index.html', indexed[0]['results']['nl-NL'])
            self.assertIn('/en/place/P1/index.html', indexed[0]['results']['en-US'])

    def test_empty(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            configuration.plugins[Search] = {}
            site = Site(configuration)

            indexed = list(index(site))

            self.assertEquals([], indexed)
