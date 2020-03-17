from tempfile import TemporaryDirectory
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Person, Place, LocalizedName, PersonName, File
from betty.config import Configuration, LocaleConfiguration
from betty.jinja2 import create_environment
from betty.search import index
from betty.site import Site


class IndexTest(TestCase):
    def test_empty(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            site = Site(configuration)
            environment = create_environment(site)

            indexed = list(index(site, environment))

            self.assertEquals([], indexed)

    def test_person_without_names(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            site = Site(configuration)
            environment = create_environment(site)
            person_id = 'P1'
            person = Person(person_id)
            site.ancestry.people[person_id] = person

            indexed = list(index(site, environment))

            self.assertEquals([], indexed)

    def test_private_person(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            site = Site(configuration)
            environment = create_environment(site)
            person_id = 'P1'
            individual_name = 'Jane'
            person = Person(person_id)
            person.names.append(PersonName(individual_name))
            person.private = True
            site.ancestry.people[person_id] = person

            indexed = list(index(site, environment))

            self.assertEquals([], indexed)

    @parameterized.expand([
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    def test_person_with_individual_name(self, expected: str, locale: str):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            with Site(configuration).with_locale(locale) as site:
                environment = create_environment(site)
                person_id = 'P1'
                individual_name = 'Jane'
                person = Person(person_id)
                person.names.append(PersonName(individual_name))
                site.ancestry.people[person_id] = person

                indexed = list(index(site, environment))

            self.assertEquals('jane', indexed[0]['text'])
            self.assertIn(expected, indexed[0]['result'])

    @parameterized.expand([
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    def test_person_with_affiliation_name(self, expected: str, locale: str):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            with Site(configuration).with_locale(locale) as site:
                environment = create_environment(site)
                person_id = 'P1'
                affiliation_name = 'Doughnut'
                person = Person(person_id)
                person.names.append(PersonName(None, affiliation_name))
                site.ancestry.people[person_id] = person

                indexed = list(index(site, environment))

            self.assertEquals('doughnut', indexed[0]['text'])
            self.assertIn(expected, indexed[0]['result'])

    @parameterized.expand([
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    def test_person_with_individual_and_affiliation_names(self, expected: str, locale: str):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            with Site(configuration).with_locale(locale) as site:
                environment = create_environment(site)
                person_id = 'P1'
                individual_name = 'Jane'
                affiliation_name = 'Doughnut'
                person = Person(person_id)
                person.names.append(PersonName(individual_name, affiliation_name))
                site.ancestry.people[person_id] = person

                indexed = list(index(site, environment))

            self.assertEquals('jane doughnut', indexed[0]['text'])
            self.assertIn(expected, indexed[0]['result'])

    @parameterized.expand([
        ('/nl/place/P1/index.html', 'nl-NL'),
        ('/en/place/P1/index.html', 'en-US'),
    ])
    def test_place(self, expected: str, locale: str):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            with Site(configuration).with_locale(locale) as site:
                environment = create_environment(site)
                place_id = 'P1'
                place = Place(place_id, [LocalizedName(
                    'Netherlands', 'en'), LocalizedName('Nederland', 'nl')])
                site.ancestry.places[place_id] = place

                indexed = list(index(site, environment))

            self.assertEquals('netherlands nederland', indexed[0]['text'])
            self.assertIn(expected, indexed[0]['result'])

    def test_file_without_description(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            site = Site(configuration)
            environment = create_environment(site)
            file_id = 'F1'
            file = File(file_id, __file__)
            site.ancestry.files[file_id] = file

            indexed = list(index(site, environment))

            self.assertEquals([], indexed)

    @parameterized.expand([
        ('/nl/file/F1/index.html', 'nl-NL'),
        ('/en/file/F1/index.html', 'en-US'),
    ])
    def test_file(self, expected: str, locale: str):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            with Site(configuration).with_locale(locale) as site:
                environment = create_environment(site)
                file_id = 'F1'
                file = File(file_id, __file__)
                file.description = '"file" is Dutch for "traffic jam"'
                site.ancestry.files[file_id] = file

                indexed = list(index(site, environment))

            self.assertEquals('"file" is dutch for "traffic jam"', indexed[0]['text'])
            self.assertIn(expected, indexed[0]['result'])
