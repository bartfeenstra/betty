from pathlib import Path

from betty.extension import CottonCandy
from betty.model.ancestry import Source, File, Citation, Person, PersonName
from betty.tests import TemplateTestCase


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/page--source.html.j2'

    async def test_privacy(self) -> None:
        source = Source(None)
        source.name = 'source name'

        public_file = File(None, Path())
        public_file.description = 'public file description'
        public_file.entities.add(source)

        private_file = File(None, Path())
        private_file.private = True
        private_file.description = 'private file description'
        private_file.entities.add(source)

        public_citation = Citation(None, source)
        public_citation.location = 'public citation location'
        public_citation.source = source

        public_file_for_public_citation = File(None, Path())
        public_file_for_public_citation.description = 'public file for public citation description'
        public_file_for_public_citation.entities.add(public_citation)

        private_file_for_public_citation = File(None, Path())
        private_file_for_public_citation.private = True
        private_file_for_public_citation.description = 'private file for public citation description'
        private_file_for_public_citation.entities.add(public_citation)

        public_fact_for_public_citation_name = 'public fact for public citation name'
        public_fact_for_public_citation = Person('FACT1')
        PersonName(None, public_fact_for_public_citation, public_fact_for_public_citation_name)
        public_fact_for_public_citation.citations.add(public_citation)

        private_fact_for_public_citation_name = 'private fact for public citation name'
        private_fact_for_public_citation = Person('FACT2')
        private_fact_for_public_citation.private = True
        PersonName(None, private_fact_for_public_citation, private_fact_for_public_citation_name)
        private_fact_for_public_citation.citations.add(public_citation)

        private_citation = Citation(None, source)
        private_citation.private = True
        private_citation.location = 'private citation location'
        private_citation.source = source

        public_file_for_private_citation = File(None, Path())
        public_file_for_private_citation.description = 'public file for private citation description'
        public_file_for_private_citation.entities.add(private_citation)

        private_file_for_private_citation = File(None, Path())
        private_file_for_private_citation.private = True
        private_file_for_private_citation.description = 'private file for private citation description'
        private_file_for_private_citation.entities.add(private_citation)

        public_fact_for_private_citation_name = 'public fact for private citation name'
        public_fact_for_private_citation = Person('FACT3')
        PersonName(None, public_fact_for_private_citation, public_fact_for_private_citation_name)
        public_fact_for_private_citation.citations.add(private_citation)

        private_fact_for_private_citation_name = 'private fact for private citation name'
        private_fact_for_private_citation = Person('FACT4')
        private_fact_for_private_citation.private = True
        PersonName(None, private_fact_for_private_citation, private_fact_for_private_citation_name)
        private_fact_for_private_citation.citations.add(private_citation)

        public_contained_source = Source(None)
        public_contained_source.name = 'public contained source name'
        public_contained_source.contained_by = source

        public_file_for_public_contained_source = File(None, Path())
        public_file_for_public_contained_source.description = 'public file for public contained source description'
        public_file_for_public_contained_source.entities.add(public_contained_source)

        private_file_for_public_contained_source = File(None, Path())
        private_file_for_public_contained_source.private = True
        private_file_for_public_contained_source.description = 'private file for public contained source description'
        private_file_for_public_contained_source.entities.add(public_contained_source)

        public_citation_for_public_contained_source = Citation(None, source)
        public_citation_for_public_contained_source.location = 'public citation for public contained source location'
        public_citation_for_public_contained_source.source = public_contained_source

        public_file_for_public_citation_for_public_contained_source = File(None, Path())
        public_file_for_public_citation_for_public_contained_source.description = 'public file for public citation for public contained source description'
        public_file_for_public_citation_for_public_contained_source.entities.add(public_citation_for_public_contained_source)

        private_file_for_public_citation_for_public_contained_source = File(None, Path())
        private_file_for_public_citation_for_public_contained_source.private = True
        private_file_for_public_citation_for_public_contained_source.description = 'private file for public citation for public contained source description'
        private_file_for_public_citation_for_public_contained_source.entities.add(public_citation_for_public_contained_source)

        public_fact_for_public_citation_for_public_contained_source_name = 'public fact for public citation for public contained source name'
        public_fact_for_public_citation_for_public_contained_source = Person('FACT5')
        PersonName(None, public_fact_for_public_citation_for_public_contained_source, public_fact_for_public_citation_for_public_contained_source_name)
        public_fact_for_public_citation_for_public_contained_source.citations.add(public_citation_for_public_contained_source)

        private_fact_for_public_citation_for_public_contained_source_name = 'private fact for public citation for public contained source name'
        private_fact_for_public_citation_for_public_contained_source = Person('FACT6')
        private_fact_for_public_citation_for_public_contained_source.private = True
        PersonName(None, private_fact_for_public_citation_for_public_contained_source, private_fact_for_public_citation_for_public_contained_source_name)
        private_fact_for_public_citation_for_public_contained_source.citations.add(public_citation_for_public_contained_source)

        private_citation_for_public_contained_source = Citation(None, source)
        private_citation_for_public_contained_source.private = True
        private_citation_for_public_contained_source.location = 'private citation for public contained source location'
        private_citation_for_public_contained_source.source = public_contained_source

        public_file_for_private_citation_for_public_contained_source = File(None, Path())
        public_file_for_private_citation_for_public_contained_source.description = 'public file for private citation for public contained source description'
        public_file_for_private_citation_for_public_contained_source.entities.add(private_citation_for_public_contained_source)

        private_file_for_private_citation_for_public_contained_source = File(None, Path())
        private_file_for_private_citation_for_public_contained_source.private = True
        private_file_for_private_citation_for_public_contained_source.description = 'private file for private citation for public contained source description'
        private_file_for_private_citation_for_public_contained_source.entities.add(private_citation_for_public_contained_source)

        public_fact_for_private_citation_for_public_contained_source_name = 'public fact for private citation for public contained source name'
        public_fact_for_private_citation_for_public_contained_source = Person('FACT7')
        PersonName(None, public_fact_for_private_citation_for_public_contained_source, public_fact_for_private_citation_for_public_contained_source_name)
        public_fact_for_private_citation_for_public_contained_source.citations.add(private_citation_for_public_contained_source)

        private_fact_for_private_citation_for_public_contained_source_name = 'private fact for private citation for public contained source name'
        private_fact_for_private_citation_for_public_contained_source = Person('FACT8')
        private_fact_for_private_citation_for_public_contained_source.private = True
        PersonName(None, private_fact_for_private_citation_for_public_contained_source, private_fact_for_private_citation_for_public_contained_source_name)
        private_fact_for_private_citation_for_public_contained_source.citations.add(private_citation_for_public_contained_source)

        private_contained_source = Source(None)
        private_contained_source.private = True
        private_contained_source.name = 'private contained source name'
        private_contained_source.contained_by = source

        public_file_for_private_contained_source = File(None, Path())
        public_file_for_private_contained_source.description = 'public file for private contained source description'
        public_file_for_private_contained_source.entities.add(private_contained_source)

        private_file_for_private_contained_source = File(None, Path())
        private_file_for_private_contained_source.private = True
        private_file_for_private_contained_source.description = 'private file for private contained source description'
        private_file_for_private_contained_source.entities.add(private_contained_source)

        public_citation_for_private_contained_source = Citation(None, source)
        public_citation_for_private_contained_source.location = 'public citation for private contained source location'
        public_citation_for_private_contained_source.source = private_contained_source

        public_file_for_public_citation_for_private_contained_source = File(None, Path())
        public_file_for_public_citation_for_private_contained_source.description = 'public file for public citation for private contained source description'
        public_file_for_public_citation_for_private_contained_source.entities.add(public_citation_for_private_contained_source)

        private_file_for_public_citation_for_private_contained_source = File(None, Path())
        private_file_for_public_citation_for_private_contained_source.private = True
        private_file_for_public_citation_for_private_contained_source.description = 'private file for public citation for private contained source description'
        private_file_for_public_citation_for_private_contained_source.entities.add(public_citation_for_private_contained_source)

        public_fact_for_public_citation_for_private_contained_source_name = 'public fact for public citation for private contained source name'
        public_fact_for_public_citation_for_private_contained_source = Person('FACT7')
        PersonName(None, public_fact_for_public_citation_for_private_contained_source, public_fact_for_public_citation_for_private_contained_source_name)
        public_fact_for_public_citation_for_private_contained_source.citations.add(public_citation_for_private_contained_source)

        private_fact_for_public_citation_for_private_contained_source_name = 'private fact for public citation for private contained source name'
        private_fact_for_public_citation_for_private_contained_source = Person('FACT8')
        private_fact_for_public_citation_for_private_contained_source.private = True
        PersonName(None, private_fact_for_public_citation_for_private_contained_source, private_fact_for_public_citation_for_private_contained_source_name)
        private_fact_for_public_citation_for_private_contained_source.citations.add(public_citation_for_private_contained_source)

        private_citation_for_private_contained_source = Citation(None, source)
        private_citation_for_private_contained_source.private = True
        private_citation_for_private_contained_source.location = 'private citation for private contained source location'
        private_citation_for_private_contained_source.source = private_contained_source

        public_file_for_private_citation_for_private_contained_source = File(None, Path())
        public_file_for_private_citation_for_private_contained_source.description = 'public file for private citation for private contained source description'
        public_file_for_private_citation_for_private_contained_source.entities.add(private_citation_for_private_contained_source)

        private_file_for_private_citation_for_private_contained_source = File(None, Path())
        private_file_for_private_citation_for_private_contained_source.private = True
        private_file_for_private_citation_for_private_contained_source.description = 'private file for private citation for private contained source description'
        private_file_for_private_citation_for_private_contained_source.entities.add(private_citation_for_private_contained_source)

        public_fact_for_private_citation_for_private_contained_source_name = 'public fact for private citation for private contained source name'
        public_fact_for_private_citation_for_private_contained_source = Person('FACT7')
        PersonName(None, public_fact_for_private_citation_for_private_contained_source, public_fact_for_private_citation_for_private_contained_source_name)
        public_fact_for_private_citation_for_private_contained_source.citations.add(private_citation_for_private_contained_source)

        private_fact_for_private_citation_for_private_contained_source_name = 'private fact for private citation for private contained source name'
        private_fact_for_private_citation_for_private_contained_source = Person('FACT8')
        private_fact_for_private_citation_for_private_contained_source.private = True
        PersonName(None, private_fact_for_private_citation_for_private_contained_source, private_fact_for_private_citation_for_private_contained_source_name)
        private_fact_for_private_citation_for_private_contained_source.citations.add(private_citation_for_private_contained_source)

        with self._render(
            data={
                'page_resource': source,
                'entity_type': Source,
                'entity': source,
            },
        ) as (actual, _):
            assert source.name in actual
            assert public_file.description in actual
            assert public_file_for_public_citation.description in actual
            assert public_file_for_public_contained_source.description in actual
            assert public_file_for_public_citation_for_public_contained_source.description in actual
            assert public_fact_for_public_citation_name in actual
            assert public_fact_for_public_citation_for_public_contained_source_name in actual

            assert private_file.description not in actual
            assert private_file_for_public_citation.description not in actual
            assert public_file_for_private_citation.description not in actual
            assert private_file_for_private_citation.description not in actual
            assert private_file_for_public_contained_source.description not in actual
            assert public_file_for_private_contained_source.description not in actual
            assert private_file_for_private_contained_source.description not in actual
            assert private_file_for_public_citation_for_public_contained_source.description not in actual
            assert public_file_for_private_citation_for_public_contained_source.description not in actual
            assert private_file_for_private_citation_for_public_contained_source.description not in actual
            assert public_file_for_public_citation_for_private_contained_source.description not in actual
            assert private_file_for_public_citation_for_private_contained_source.description not in actual
            assert public_file_for_private_citation_for_private_contained_source.description not in actual
            assert private_file_for_private_citation_for_private_contained_source.description not in actual
            assert private_fact_for_public_citation_name not in actual
            assert public_fact_for_private_citation_name not in actual
            assert private_fact_for_private_citation_name not in actual
            assert private_fact_for_public_citation_for_public_contained_source_name not in actual
            assert public_fact_for_private_citation_for_public_contained_source_name not in actual
            assert private_fact_for_private_citation_for_public_contained_source_name not in actual
            assert public_fact_for_public_citation_for_private_contained_source_name not in actual
            assert private_fact_for_public_citation_for_private_contained_source_name not in actual
            assert public_fact_for_private_citation_for_private_contained_source_name not in actual
            assert private_fact_for_private_citation_for_private_contained_source_name not in actual
