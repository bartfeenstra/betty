from parameterized import parameterized

from betty.app import App
from betty.asyncio import sync
from betty.model.ancestry import Person, Place, PlaceName, PersonName, File
from betty.project import LocaleConfiguration
from betty.search import Index
from betty.tests import TestCase


class IndexTest(TestCase):
    @sync
    async def test_empty(self):
        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            indexed = [item for item in Index(app).build()]

        self.assertEqual([], indexed)

    @sync
    async def test_person_without_names(self):
        person_id = 'P1'
        person = Person(person_id)

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            app.project.ancestry.entities.append(person)
            indexed = [item for item in Index(app).build()]

        self.assertEqual([], indexed)

    @sync
    async def test_private_person(self):
        person_id = 'P1'
        individual_name = 'Jane'
        person = Person(person_id)
        PersonName(person, individual_name)
        person.private = True

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            app.project.ancestry.entities.append(person)
            indexed = [item for item in Index(app).build()]

        self.assertEqual([], indexed)

    @parameterized.expand([
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    @sync
    async def test_person_with_individual_name(self, expected: str, locale: str):
        person_id = 'P1'
        individual_name = 'Jane'
        person = Person(person_id)
        PersonName(person, individual_name)

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            with app.activate_locale(locale):
                app.project.ancestry.entities.append(person)
                indexed = [item for item in Index(app).build()]

        self.assertEqual('jane', indexed[0]['text'])
        self.assertIn(expected, indexed[0]['result'])

    @parameterized.expand([
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    @sync
    async def test_person_with_affiliation_name(self, expected: str, locale: str):
        person_id = 'P1'
        affiliation_name = 'Doughnut'
        person = Person(person_id)
        PersonName(person, None, affiliation_name)

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            with app.activate_locale(locale):
                app.project.ancestry.entities.append(person)
                indexed = [item for item in Index(app).build()]

        self.assertEqual('doughnut', indexed[0]['text'])
        self.assertIn(expected, indexed[0]['result'])

    @parameterized.expand([
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    @sync
    async def test_person_with_individual_and_affiliation_names(self, expected: str, locale: str):
        person_id = 'P1'
        individual_name = 'Jane'
        affiliation_name = 'Doughnut'
        person = Person(person_id)
        PersonName(person, individual_name, affiliation_name)

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            with app.activate_locale(locale):
                app.project.ancestry.entities.append(person)
                indexed = [item for item in Index(app).build()]

        self.assertEqual('jane doughnut', indexed[0]['text'])
        self.assertIn(expected, indexed[0]['result'])

    @parameterized.expand([
        ('/nl/place/P1/index.html', 'nl-NL'),
        ('/en/place/P1/index.html', 'en-US'),
    ])
    @sync
    async def test_place(self, expected: str, locale: str):
        place_id = 'P1'
        place = Place(place_id, [PlaceName('Netherlands', 'en'), PlaceName('Nederland', 'nl')])

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            with app.activate_locale(locale):
                app.project.ancestry.entities.append(place)
                indexed = [item for item in Index(app).build()]

        self.assertEqual('netherlands nederland', indexed[0]['text'])
        self.assertIn(expected, indexed[0]['result'])

    @sync
    async def test_file_without_description(self):
        file_id = 'F1'
        file = File(file_id, __file__)

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            app.project.ancestry.entities.append(file)
            indexed = [item for item in Index(app).build()]

        self.assertEqual([], indexed)

    @parameterized.expand([
        ('/nl/file/F1/index.html', 'nl-NL'),
        ('/en/file/F1/index.html', 'en-US'),
    ])
    @sync
    async def test_file(self, expected: str, locale: str):
        file_id = 'F1'
        file = File(file_id, __file__)
        file.description = '"file" is Dutch for "traffic jam"'

        app = App()
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        async with app:
            with app.activate_locale(locale):
                app.project.ancestry.entities.append(file)
                indexed = [item for item in Index(app).build()]

        self.assertEqual('"file" is dutch for "traffic jam"', indexed[0]['text'])
        self.assertIn(expected, indexed[0]['result'])
