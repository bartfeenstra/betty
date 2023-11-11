from pathlib import Path

from betty.extension import CottonCandy
from betty.model.ancestry import Citation, Source, File, Person, PersonName
from betty.tests import TemplateTestCase


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/page--citation.html.j2'

    async def test_privacy(self) -> None:
        source = Source(None)
        source.name = 'source name'

        citation = Citation(None, source)
        citation.location = 'citation location'

        public_file = File(None, Path())
        public_file.description = 'public file description'
        public_file.entities.add(citation)

        private_file = File(None, Path())
        private_file.private = True
        private_file.description = 'private file description'
        private_file.entities.add(citation)

        public_fact_name = 'public fact'
        public_fact = Person('FACT1')
        PersonName(None, public_fact, public_fact_name)
        citation.facts.add(public_fact)

        private_fact_name = 'private fact'
        private_fact = Person('FACT2')
        private_fact.private = True
        PersonName(None, private_fact, private_fact_name)
        citation.facts.add(private_fact)

        async with self._render(
            data={
                'page_resource': citation,
                'entity_type': Citation,
                'entity': citation,
            },
        ) as (actual, _):
            assert citation.location in actual
            assert public_file.description in actual
            assert public_fact_name in actual

            assert private_file.description not in actual
            assert private_fact_name not in actual
