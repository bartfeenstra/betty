import pytest

from betty.app import App
from betty.cotton_candy import CottonCandy
from betty.cotton_candy.search import Index
from betty.model.ancestry import Person, Place, PlaceName, PersonName, File
from betty.project import LocaleConfiguration


class TestIndex:
    def test_empty(self):
        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            indexed = [item for item in Index(app).build()]

        assert [] == indexed

    def test_person_without_names(self):
        person_id = 'P1'
        person = Person(person_id)

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            app.project.ancestry.entities.append(person)
            indexed = [item for item in Index(app).build()]

        assert [] == indexed

    def test_private_person(self):
        person_id = 'P1'
        individual_name = 'Jane'
        person = Person(person_id)
        PersonName(person, individual_name)
        person.private = True

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            app.project.ancestry.entities.append(person)
            indexed = [item for item in Index(app).build()]

        assert [] == indexed

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    def test_person_with_individual_name(self, expected: str, locale: str):
        person_id = 'P1'
        individual_name = 'Jane'
        person = Person(person_id)
        PersonName(person, individual_name)

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            with app.acquire_locale(locale):
                app.project.ancestry.entities.append(person)
                indexed = [item for item in Index(app).build()]

        assert 'jane' == indexed[0]['text']
        assert expected in indexed[0]['result']

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    def test_person_with_affiliation_name(self, expected: str, locale: str):
        person_id = 'P1'
        affiliation_name = 'Doughnut'
        person = Person(person_id)
        PersonName(person, None, affiliation_name)

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            with app.acquire_locale(locale):
                app.project.ancestry.entities.append(person)
                indexed = [item for item in Index(app).build()]

        assert 'doughnut' == indexed[0]['text']
        assert expected in indexed[0]['result']

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/person/P1/index.html', 'nl-NL'),
        ('/en/person/P1/index.html', 'en-US'),
    ])
    def test_person_with_individual_and_affiliation_names(self, expected: str, locale: str):
        person_id = 'P1'
        individual_name = 'Jane'
        affiliation_name = 'Doughnut'
        person = Person(person_id)
        PersonName(person, individual_name, affiliation_name)

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            with app.acquire_locale(locale):
                app.project.ancestry.entities.append(person)
                indexed = [item for item in Index(app).build()]

        assert 'jane doughnut' == indexed[0]['text']
        assert expected in indexed[0]['result']

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/place/P1/index.html', 'nl-NL'),
        ('/en/place/P1/index.html', 'en-US'),
    ])
    def test_place(self, expected: str, locale: str):
        place_id = 'P1'
        place = Place(place_id, [PlaceName('Netherlands', 'en'), PlaceName('Nederland', 'nl')])

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            with app.acquire_locale(locale):
                app.project.ancestry.entities.append(place)
                indexed = [item for item in Index(app).build()]

        assert 'netherlands nederland' == indexed[0]['text']
        assert expected in indexed[0]['result']

    def test_file_without_description(self):
        file_id = 'F1'
        file = File(file_id, __file__)

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            app.project.ancestry.entities.append(file)
            indexed = [item for item in Index(app).build()]

        assert [] == indexed

    @pytest.mark.parametrize('expected, locale', [
        ('/nl/file/F1/index.html', 'nl-NL'),
        ('/en/file/F1/index.html', 'en-US'),
    ])
    def test_file(self, expected: str, locale: str):
        file_id = 'F1'
        file = File(file_id, __file__)
        file.description = '"file" is Dutch for "traffic jam"'

        app = App()
        app.project.configuration.extensions.enable(CottonCandy)
        app.project.configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        ])
        with app:
            with app.acquire_locale(locale):
                app.project.ancestry.entities.append(file)
                indexed = [item for item in Index(app).build()]

        assert '"file" is dutch for "traffic jam"' == indexed[0]['text']
        assert expected in indexed[0]['result']
