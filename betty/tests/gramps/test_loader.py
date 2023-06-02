from pathlib import Path
from typing import Optional

import pytest

from betty.app import App
from betty.gramps.loader import load_xml, load_gpkg, load_gramps
from betty.locale import Date, DateRange
from betty.model.ancestry import Ancestry, PersonName, Citation, Note, Source, File, Event, Person, Place
from betty.model.event_type import Birth, Death, UnknownEventType
from betty.path import rootname
from betty.tempfile import TemporaryDirectory


class TestLoadGramps:
    def test_load_gramps(self):
        with App() as app:
            gramps_file_path = Path(__file__).parent / 'assets' / 'minimal.gramps'
            load_gramps(app.project.ancestry, gramps_file_path)


class TestLoadGpkg:
    def test_load_gpkg(self):
        with App() as app:
            gramps_file_path = Path(__file__).parent / 'assets' / 'minimal.gpkg'
            load_gpkg(app.project.ancestry, gramps_file_path)


@pytest.fixture(scope='class')
def test_load_xml_ancestry() -> Ancestry:
    # @todo Convert each test method to use self._load(), so we can remove this shared XML file.
    with App() as app:
        xml_file_path = Path(__file__).parent / 'assets' / 'data.xml'
        with open(xml_file_path) as f:
            load_xml(app.project.ancestry, f.read(), rootname(xml_file_path))
    return app.project.ancestry


class TestLoadXml:
    def load(self, xml: str) -> Ancestry:
        with App() as app:
            with TemporaryDirectory() as tree_directory_path:
                load_xml(app.project.ancestry, xml.strip(), tree_directory_path)
                return app.project.ancestry

    def _load_partial(self, xml: str) -> Ancestry:
        return self.load("""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
  <header>
    <created date="2019-03-09" version="4.2.8"/>
    <researcher>
    </researcher>
  </header>
  %s
</database>
""" % xml)

    def test_load_xml_with_string(self):
        with App() as app:
            gramps_file_path = Path(__file__).parent / 'assets' / 'minimal.xml'
            with open(gramps_file_path) as f:
                load_xml(app.project.ancestry, f.read(), rootname(gramps_file_path))

    def test_load_xml_with_file_path(self):
        with App() as app:
            gramps_file_path = Path(__file__).parent / 'assets' / 'minimal.xml'
            load_xml(app.project.ancestry, gramps_file_path, rootname(gramps_file_path))

    def test_place_should_include_name(self, test_load_xml_ancestry):
        place = test_load_xml_ancestry.entities[Place]['P0000']
        names = place.names
        assert 1 == len(names)
        name = names[0]
        assert 'Amsterdam' == name.name

    @pytest.mark.parametrize('expected_latitude, expected_longitude, latitude, longitude', [
        (4.9, 52.366667, '4.9', '52.366667'),
        (41.5, -81.0, '41.5', '-81.0'),
        (41.5, 81.0, '41.5 N', '-81.0 W'),
        (41.5, 81.0, '-41.5 S', '81.0 E'),
        (23.439444, 23.458333, '23 26m 22s N', '23 27m 30s E'),
        (39.333333, -74.583333, "N 39°20' 0''", "W 74°35' 0''"),
    ])
    def test_place_should_include_coordinates(
            self,
            expected_latitude: float,
            expected_longitude: float,
            latitude: str,
            longitude: str,
    ):
        ancestry = self._load_partial(f"""
        <places>
        <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
          <coord lat="{latitude}" long="{longitude}"/>
        </placeobj>
        </places>
        """)
        coordinates = ancestry.entities[Place]['P0000'].coordinates
        assert coordinates
        assert pytest.approx(expected_latitude) == coordinates.latitude
        assert pytest.approx(expected_longitude) == coordinates.longitude

    def test_place_should_ignore_invalid_coordinates(self):
        ancestry = self._load_partial("""
        <places>
        <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
          <coord lat="foo" long="bar"/>
        </placeobj>
        </places>
        """)
        coordinates = ancestry.entities[Place]['P0000'].coordinates
        assert coordinates is None

    def test_place_should_include_events(self, test_load_xml_ancestry):
        place = test_load_xml_ancestry.entities[Place]['P0000']
        event = test_load_xml_ancestry.entities[Event]['E0000']
        assert place == event.place
        assert event in place.events

    def test_place_should_include_enclosed_by(self):
        ancestry = self._load_partial("""
<places>
    <placeobj handle="_e7692ea23775e80643fe4fcf91" change="1552125653" id="P0000" type="Unknown">
    </placeobj>
    <placeobj handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1552125653" id="P0001" type="Unknown">
    </placeobj>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0002" type="Unknown">
        <placeref hlink="_e7692ea23775e80643fe4fcf91"/>
        <placeref hlink="_e2b5e77b4cc5c91c9ed60a6cb39"/>
    </placeobj>
</places>
""")
        assert ancestry.entities[Place]['P0000'] == ancestry.entities[Place]['P0002'].enclosed_by[0].enclosed_by
        assert ancestry.entities[Place]['P0001'] == ancestry.entities[Place]['P0002'].enclosed_by[1].enclosed_by
        assert ancestry.entities[Place]['P0002'] == ancestry.entities[Place]['P0000'].encloses[0].encloses
        assert ancestry.entities[Place]['P0002'] == ancestry.entities[Place]['P0001'].encloses[0].encloses

    def test_person_should_include_name(self, test_load_xml_ancestry):
        person = test_load_xml_ancestry.entities[Person]['I0000']
        expected = PersonName(person, 'Jane', 'Doe')
        assert expected == person.name

    def test_person_should_include_alternative_names(self, test_load_xml_ancestry):
        person = test_load_xml_ancestry.entities[Person]['I0000']
        assert 3 == len(person.alternative_names)
        assert person is person.alternative_names[0].person
        assert 'Jane' == person.alternative_names[0].individual
        assert 'Doh' == person.alternative_names[0].affiliation
        assert person is person.alternative_names[1].person
        assert 'Jen' == person.alternative_names[1].individual
        assert 'Van Doughie' == person.alternative_names[1].affiliation
        assert person is person.alternative_names[2].person
        assert 'Jane' == person.alternative_names[2].individual
        assert 'Doe' == person.alternative_names[2].affiliation

    def test_person_should_include_birth(self, test_load_xml_ancestry):
        person = test_load_xml_ancestry.entities[Person]['I0000']
        assert 'E0000' == person.start.id

    def test_person_should_include_death(self, test_load_xml_ancestry):
        person = test_load_xml_ancestry.entities[Person]['I0003']
        assert 'E0002' == person.end.id

    def test_person_should_be_private(self, test_load_xml_ancestry):
        person = test_load_xml_ancestry.entities[Person]['I0003']
        assert person.private

    def test_person_should_not_be_private(self, test_load_xml_ancestry):
        person = test_load_xml_ancestry.entities[Person]['I0002']
        assert not person.private

    def test_person_should_include_citation(self, test_load_xml_ancestry):
        person = test_load_xml_ancestry.entities[Person]['I0000']
        citation = test_load_xml_ancestry.entities[Citation]['C0000']
        assert citation in person.citations

    def test_family_should_set_parents(self, test_load_xml_ancestry):
        expected_parents = [
            test_load_xml_ancestry.entities[Person]['I0002'],
            test_load_xml_ancestry.entities[Person]['I0003'],
        ]
        children = [
            test_load_xml_ancestry.entities[Person]['I0000'],
            test_load_xml_ancestry.entities[Person]['I0001'],
        ]
        for child in children:
            assert sorted(expected_parents) == sorted(child.parents)

    def test_family_should_set_children(self, test_load_xml_ancestry):
        parents = [
            test_load_xml_ancestry.entities[Person]['I0002'],
            test_load_xml_ancestry.entities[Person]['I0003'],
        ]
        expected_children = [
            test_load_xml_ancestry.entities[Person]['I0000'],
            test_load_xml_ancestry.entities[Person]['I0001'],
        ]
        for parent in parents:
            assert sorted(expected_children) == sorted(parent.children)

    def test_event_should_be_birth(self, test_load_xml_ancestry):
        assert issubclass(test_load_xml_ancestry.entities[Event]['E0000'].type, Birth)

    def test_event_should_be_death(self, test_load_xml_ancestry):
        assert issubclass(test_load_xml_ancestry.entities[Event]['E0002'].type, Death)

    def test_event_should_load_unknown(self, test_load_xml_ancestry):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>SomeEventThatIUsedToKnow</type>
        <dateval val="0000-00-00" quality="calculated"/>
    </event>
</events>
""")
        assert issubclass(ancestry.entities[Event]['E0000'].type, UnknownEventType)

    def test_event_should_include_place(self, test_load_xml_ancestry):
        event = test_load_xml_ancestry.entities[Event]['E0000']
        place = test_load_xml_ancestry.entities[Place]['P0000']
        assert place == event.place

    def test_event_should_include_date(self, test_load_xml_ancestry):
        event = test_load_xml_ancestry.entities[Event]['E0000']
        assert 1970 == event.date.year
        assert 1 == event.date.month
        assert 1 == event.date.day

    def test_event_should_include_people(self, test_load_xml_ancestry):
        event = test_load_xml_ancestry.entities[Event]['E0000']
        expected_people = [test_load_xml_ancestry.entities[Person]['I0000']]
        assert expected_people == [presence.person for presence in event.presences]

    def test_event_should_include_description(self, test_load_xml_ancestry):
        event = test_load_xml_ancestry.entities[Event]['E0008']
        assert 'Something happened!' == event.description

    @pytest.mark.parametrize('expected, dateval_val', [
        (Date(), '0000-00-00'),
        (Date(None, None, 1), '0000-00-01'),
        (Date(None, 1), '0000-01-00'),
        (Date(None, 1, 1), '0000-01-01'),
        (Date(1970), '1970-00-00'),
        (Date(1970, None, 1), '1970-00-01'),
        (Date(1970, 1), '1970-01-00'),
        (Date(1970, 1, 1), '1970-01-01'),
    ])
    def test_date_should_load_parts(self, expected: Date, dateval_val: str):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="%s" quality="calculated"/>
    </event>
</events>
""" % dateval_val)
        assert expected == ancestry.entities[Event]['E0000'].date

    def test_date_should_ignore_calendar_format(self, test_load_xml_ancestry):
        assert test_load_xml_ancestry.entities[Event]['E0005'].date is None

    def test_date_should_load_before(self, test_load_xml_ancestry):
        date = test_load_xml_ancestry.entities[Event]['E0003'].date
        assert date.start is None
        assert 1970 == date.end.year
        assert 1 == date.end.month
        assert 1 == date.end.day
        assert date.end_is_boundary
        assert not date.end.fuzzy

    def test_date_should_load_after(self, test_load_xml_ancestry):
        date = test_load_xml_ancestry.entities[Event]['E0004'].date
        assert date.end is None
        assert 1970 == date.start.year
        assert 1 == date.start.month
        assert 1 == date.start.day
        assert date.start_is_boundary
        assert not date.start.fuzzy

    def test_date_should_load_calculated(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" quality="calculated"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, Date)
        assert 1970 == date.year
        assert 1 == date.month
        assert 1 == date.day
        assert not date.fuzzy

    def test_date_should_load_estimated(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" quality="estimated"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, Date)
        assert 1970 == date.year
        assert 1 == date.month
        assert 1 == date.day
        assert date.fuzzy

    def test_date_should_load_about(self, test_load_xml_ancestry):
        date = test_load_xml_ancestry.entities[Event]['E0007'].date
        assert 1970 == date.year
        assert 1 == date.month
        assert 1 == date.day
        assert date.fuzzy

    def test_daterange_should_load(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        end = date.end
        assert isinstance(end, Date)
        assert 1970 == start.year
        assert 1 == start.month
        assert 1 == start.day
        assert not start.fuzzy
        assert date.start_is_boundary
        assert 1999 == end.year
        assert 12 == end.month
        assert 31 == end.day
        assert date.end_is_boundary
        assert not end.fuzzy

    def test_daterange_should_load_calculated(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31" quality="calculated"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert not start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert not end.fuzzy

    def test_daterange_should_load_estimated(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31" quality="estimated"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert end.fuzzy

    def test_datespan_should_load(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        end = date.end
        assert isinstance(end, Date)
        assert 1970 == start.year
        assert 1 == start.month
        assert 1 == start.day
        assert not start.fuzzy
        assert 1999 == end.year
        assert 12 == end.month
        assert 31 == end.day
        assert not end.fuzzy

    def test_datespan_should_load_calculated(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31" quality="calculated"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert not start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert not end.fuzzy

    def test_datespan_should_load_estimated(self):
        ancestry = self._load_partial("""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31" quality="estimated"/>
    </event>
</events>
""")
        date = ancestry.entities[Event]['E0000'].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert end.fuzzy

    def test_source_from_repository_should_include_name(self, test_load_xml_ancestry):
        source = test_load_xml_ancestry.entities[Source]['R0000']
        assert 'Library of Alexandria' == source.name

    def test_source_from_repository_should_include_link(self, test_load_xml_ancestry):
        links = test_load_xml_ancestry.entities[Source]['R0000'].links
        assert 1 == len(links)
        link = list(links)[0]
        assert 'https://alexandria.example.com' == link.url
        assert 'Library of Alexandria Catalogue' == link.label

    def test_source_from_source_should_include_title(self, test_load_xml_ancestry):
        source = test_load_xml_ancestry.entities[Source]['S0000']
        assert 'A Whisper' == source.name

    def test_source_from_source_should_include_author(self, test_load_xml_ancestry):
        source = test_load_xml_ancestry.entities[Source]['S0000']
        assert 'A Little Birdie' == source.author

    def test_source_from_source_should_include_publisher(self, test_load_xml_ancestry):
        source = test_load_xml_ancestry.entities[Source]['S0000']
        assert 'Somewhere over the rainbow' == source.publisher

    def test_source_from_source_should_include_repository(self, test_load_xml_ancestry):
        source = test_load_xml_ancestry.entities[Source]['S0000']
        containing_source = test_load_xml_ancestry.entities[Source]['R0000']
        assert containing_source == source.contained_by

    @pytest.mark.parametrize('expected, attribute_value', [
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_person_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._load_partial("""
<people>
    <person handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="I0000">
        <gender>U</gender>
        <attribute type="betty:privacy" value="%s"/>
    </person>
</people>
""" % attribute_value)
        person = ancestry.entities[Person]['I0000']
        assert expected == person.private

    @pytest.mark.parametrize('expected, attribute_value', [
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_event_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._load_partial("""
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
        <attribute type="betty:privacy" value="%s"/>
    </event>
</events>
""" % attribute_value)
        event = ancestry.entities[Event]['E0000']
        assert expected == event.private

    @pytest.mark.parametrize('expected, attribute_value', [
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_file_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._load_partial("""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <attribute type="betty:privacy" value="%s"/>
    </object>
</objects>
""" % attribute_value)
        file = ancestry.entities[File]['O0000']
        assert expected == file.private

    @pytest.mark.parametrize('expected, attribute_value', [
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_source_from_source_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._load_partial("""
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
        <srcattribute type="betty:privacy" value="%s"/>
    </source>
</sources>
""" % attribute_value)
        source = ancestry.entities[Source]['S0000']
        assert expected == source.private

    @pytest.mark.parametrize('expected, attribute_value', [
        (True, 'private'),
        (False, 'public'),
        (None, 'publi'),
        (None, 'privat'),
    ])
    def test_citation_should_include_privacy_from_attribute(self, expected: Optional[bool], attribute_value: str) -> None:
        ancestry = self._load_partial("""
<citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0000">
        <confidence>2</confidence>
        <sourceref hlink="_e1dd686b04813540eb3503a342b"/>
        <srcattribute type="betty:privacy" value="%s"/>
    </citation>
</citations>
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
    </source>
</sources>
""" % attribute_value)
        citation = ancestry.entities[Citation]['C0000']
        assert expected == citation.private

    def test_note_should_include_text(self) -> None:
        ancestry = self._load_partial("""
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
""")
        note = ancestry.entities[Note]['N0000']
        assert 'I left this for you.' == note.text
