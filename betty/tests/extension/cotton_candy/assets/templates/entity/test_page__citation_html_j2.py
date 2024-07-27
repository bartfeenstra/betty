from pathlib import Path

from betty.extension.cotton_candy import CottonCandy
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.locale.localizable import static
from betty.model.ancestry import (
    Citation,
    Source,
    File,
    Person,
    PersonName,
    FileReference,
)
from betty.tests import TemplateTestCase


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = "entity/page--citation.html.j2"

    async def test_privacy(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file"
        file_path.touch()

        source = Source()
        source.name = "source name"

        citation = Citation(
            source=source,
            location=static("citation location"),
        )

        public_file = File(
            path=file_path,
            description="public file description",
        )
        FileReference(citation, public_file)

        private_file = File(
            path=file_path,
            private=True,
            description="private file description",
        )
        FileReference(citation, private_file)

        public_fact_name = "public fact"
        public_fact = Person(id="FACT1")
        PersonName(
            person=public_fact,
            individual=public_fact_name,
        )
        citation.facts.add(public_fact)

        private_fact_name = "private fact"
        private_fact = Person(
            id="FACT2",
            private=True,
        )
        PersonName(
            person=private_fact,
            individual=private_fact_name,
        )
        citation.facts.add(private_fact)

        async with self._render(
            data={
                "page_resource": citation,
                "entity_type": Citation,
                "entity": citation,
            },
        ) as (actual, _):
            assert citation.location is not None
            assert citation.location.localize(DEFAULT_LOCALIZER) in actual
            assert public_file.description is not None
            assert public_file.description in actual
            assert public_fact_name in actual

            assert private_file.description is not None
            assert private_file.description not in actual
            assert private_fact_name not in actual
