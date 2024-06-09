from pathlib import Path

from betty.extension.cotton_candy import CottonCandy
from betty.locale.localizable import plain
from betty.model.ancestry import (
    Source,
    File,
    Citation,
    Person,
    PersonName,
    FileReference,
)
from betty.tests import TemplateTestCase


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = "entity/page--source.html.j2"

    async def test_privacy(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file"
        file_path.touch()

        source = Source()
        source.name = "source name"

        public_file = File(
            path=file_path,
            description="public file description",
        )
        FileReference(source, public_file)

        private_file = File(
            path=file_path,
            private=True,
            description="private file description",
        )
        FileReference(source, private_file)

        public_citation = Citation(
            source=source,
            location=plain("public citation location"),
        )
        public_citation.source = source

        public_file_for_public_citation = File(
            path=file_path,
            description="public file for public citation description",
        )
        FileReference(public_citation, public_file_for_public_citation)

        private_file_for_public_citation = File(
            path=file_path,
            private=True,
            description="private file for public citation description",
        )
        FileReference(public_citation, private_file_for_public_citation)

        public_fact_for_public_citation_name = "public fact for public citation name"
        public_fact_for_public_citation = Person(id="FACT1")
        PersonName(
            person=public_fact_for_public_citation,
            individual=public_fact_for_public_citation_name,
        )
        public_fact_for_public_citation.citations.add(public_citation)

        private_fact_for_public_citation_name = "private fact for public citation name"
        private_fact_for_public_citation = Person(
            id="FACT2",
            private=True,
        )
        PersonName(
            person=private_fact_for_public_citation,
            individual=private_fact_for_public_citation_name,
        )
        private_fact_for_public_citation.citations.add(public_citation)

        private_citation = Citation(
            source=source,
            private=True,
            location=plain("private citation location"),
        )
        private_citation.source = source

        public_file_for_private_citation = File(
            path=file_path,
            description="public file for private citation description",
        )
        FileReference(private_citation, public_file_for_private_citation)

        private_file_for_private_citation = File(
            path=file_path,
            private=True,
            description="private file for private citation description",
        )
        FileReference(private_citation, private_file_for_private_citation)

        public_fact_for_private_citation_name = "public fact for private citation name"
        public_fact_for_private_citation = Person(id="FACT3")
        PersonName(
            person=public_fact_for_private_citation,
            individual=public_fact_for_private_citation_name,
        )
        public_fact_for_private_citation.citations.add(private_citation)

        private_fact_for_private_citation_name = (
            "private fact for private citation name"
        )
        private_fact_for_private_citation = Person(
            id="FACT4",
            private=True,
        )
        PersonName(
            person=private_fact_for_private_citation,
            individual=private_fact_for_private_citation_name,
        )
        private_fact_for_private_citation.citations.add(private_citation)

        public_contained_source = Source(name="public contained source name")
        public_contained_source.contained_by = source

        public_file_for_public_contained_source = File(
            path=file_path,
            description="public file for public contained source description",
        )
        FileReference(public_contained_source, public_file_for_public_contained_source)

        private_file_for_public_contained_source = File(
            path=file_path,
            private=True,
            description="private file for public contained source description",
        )
        FileReference(public_contained_source, private_file_for_public_contained_source)

        public_citation_for_public_contained_source = Citation(
            source=source,
            location=plain("public citation for public contained source location"),
        )
        public_citation_for_public_contained_source.source = public_contained_source

        public_file_for_public_citation_for_public_contained_source = File(
            path=file_path,
            description="public file for public citation for public contained source description",
        )
        FileReference(
            public_citation_for_public_contained_source,
            public_file_for_public_citation_for_public_contained_source,
        )

        private_file_for_public_citation_for_public_contained_source = File(
            path=file_path,
            private=True,
            description="private file for public citation for public contained source description",
        )
        FileReference(
            public_citation_for_public_contained_source,
            private_file_for_public_citation_for_public_contained_source,
        )

        public_fact_for_public_citation_for_public_contained_source_name = (
            "public fact for public citation for public contained source name"
        )
        public_fact_for_public_citation_for_public_contained_source = Person(id="FACT5")
        PersonName(
            person=public_fact_for_public_citation_for_public_contained_source,
            individual=public_fact_for_public_citation_for_public_contained_source_name,
        )
        public_fact_for_public_citation_for_public_contained_source.citations.add(
            public_citation_for_public_contained_source
        )

        private_fact_for_public_citation_for_public_contained_source_name = (
            "private fact for public citation for public contained source name"
        )
        private_fact_for_public_citation_for_public_contained_source = Person(
            id="FACT6",
            private=True,
        )
        PersonName(
            person=private_fact_for_public_citation_for_public_contained_source,
            individual=private_fact_for_public_citation_for_public_contained_source_name,
        )
        private_fact_for_public_citation_for_public_contained_source.citations.add(
            public_citation_for_public_contained_source
        )

        private_citation_for_public_contained_source = Citation(
            source=source,
            private=True,
            location=plain("private citation for public contained source location"),
        )
        private_citation_for_public_contained_source.source = public_contained_source

        public_file_for_private_citation_for_public_contained_source = File(
            path=file_path,
            description="public file for private citation for public contained source description",
        )
        FileReference(
            private_citation_for_public_contained_source,
            public_file_for_private_citation_for_public_contained_source,
        )

        private_file_for_private_citation_for_public_contained_source = File(
            path=file_path,
            private=True,
            description="private file for private citation for public contained source description",
        )
        FileReference(
            private_citation_for_public_contained_source,
            private_file_for_private_citation_for_public_contained_source,
        )

        public_fact_for_private_citation_for_public_contained_source_name = (
            "public fact for private citation for public contained source name"
        )
        public_fact_for_private_citation_for_public_contained_source = Person(
            id="FACT7"
        )
        PersonName(
            person=public_fact_for_private_citation_for_public_contained_source,
            individual=public_fact_for_private_citation_for_public_contained_source_name,
        )
        public_fact_for_private_citation_for_public_contained_source.citations.add(
            private_citation_for_public_contained_source
        )

        private_fact_for_private_citation_for_public_contained_source_name = (
            "private fact for private citation for public contained source name"
        )
        private_fact_for_private_citation_for_public_contained_source = Person(
            id="FACT8",
            private=True,
        )
        PersonName(
            person=private_fact_for_private_citation_for_public_contained_source,
            individual=private_fact_for_private_citation_for_public_contained_source_name,
        )
        private_fact_for_private_citation_for_public_contained_source.citations.add(
            private_citation_for_public_contained_source
        )

        private_contained_source = Source(
            name="private contained source name",
            contained_by=source,
            private=True,
        )

        public_file_for_private_contained_source = File(
            path=file_path,
            description="public file for private contained source description",
        )
        FileReference(
            private_contained_source, public_file_for_private_contained_source
        )

        private_file_for_private_contained_source = File(
            path=file_path,
            private=True,
            description="private file for private contained source description",
        )
        FileReference(
            private_contained_source, private_file_for_private_contained_source
        )

        public_citation_for_private_contained_source = Citation(
            source=source,
            location=plain("public citation for private contained source location"),
        )
        public_citation_for_private_contained_source.source = private_contained_source

        public_file_for_public_citation_for_private_contained_source = File(
            path=file_path,
            description="public file for public citation for private contained source description",
        )
        FileReference(
            public_citation_for_private_contained_source,
            public_file_for_public_citation_for_private_contained_source,
        )

        private_file_for_public_citation_for_private_contained_source = File(
            path=file_path,
            private=True,
            description="private file for public citation for private contained source description",
        )
        FileReference(
            public_citation_for_private_contained_source,
            private_file_for_public_citation_for_private_contained_source,
        )

        public_fact_for_public_citation_for_private_contained_source_name = (
            "public fact for public citation for private contained source name"
        )
        public_fact_for_public_citation_for_private_contained_source = Person(
            id="FACT7"
        )
        PersonName(
            person=public_fact_for_public_citation_for_private_contained_source,
            individual=public_fact_for_public_citation_for_private_contained_source_name,
        )
        public_fact_for_public_citation_for_private_contained_source.citations.add(
            public_citation_for_private_contained_source
        )

        private_fact_for_public_citation_for_private_contained_source_name = (
            "private fact for public citation for private contained source name"
        )
        private_fact_for_public_citation_for_private_contained_source = Person(
            id="FACT8",
            private=True,
        )
        PersonName(
            person=private_fact_for_public_citation_for_private_contained_source,
            individual=private_fact_for_public_citation_for_private_contained_source_name,
        )
        private_fact_for_public_citation_for_private_contained_source.citations.add(
            public_citation_for_private_contained_source
        )

        private_citation_for_private_contained_source = Citation(
            source=source,
            private=True,
            location=plain("private citation for private contained source location"),
        )
        private_citation_for_private_contained_source.source = private_contained_source

        public_file_for_private_citation_for_private_contained_source = File(
            path=file_path,
            description="public file for private citation for private contained source description",
        )
        FileReference(
            private_citation_for_private_contained_source,
            public_file_for_private_citation_for_private_contained_source,
        )

        private_file_for_private_citation_for_private_contained_source = File(
            path=file_path,
            private=True,
            description="private file for private citation for private contained source description",
        )
        FileReference(
            private_citation_for_private_contained_source,
            private_file_for_private_citation_for_private_contained_source,
        )

        public_fact_for_private_citation_for_private_contained_source_name = (
            "public fact for private citation for private contained source name"
        )
        public_fact_for_private_citation_for_private_contained_source = Person(
            id="FACT7"
        )
        PersonName(
            person=public_fact_for_private_citation_for_private_contained_source,
            individual=public_fact_for_private_citation_for_private_contained_source_name,
        )
        public_fact_for_private_citation_for_private_contained_source.citations.add(
            private_citation_for_private_contained_source
        )

        private_fact_for_private_citation_for_private_contained_source_name = (
            "private fact for private citation for private contained source name"
        )
        private_fact_for_private_citation_for_private_contained_source = Person(
            id="FACT8",
            private=True,
        )
        PersonName(
            person=private_fact_for_private_citation_for_private_contained_source,
            individual=private_fact_for_private_citation_for_private_contained_source_name,
        )
        private_fact_for_private_citation_for_private_contained_source.citations.add(
            private_citation_for_private_contained_source
        )

        async with self._render(
            data={
                "page_resource": source,
                "entity_type": Source,
                "entity": source,
            },
        ) as (actual, _):
            assert source.name in actual
            assert public_file.description is not None
            assert public_file.description in actual
            assert public_file_for_public_citation.description is not None
            assert public_file_for_public_citation.description in actual
            assert public_file_for_public_contained_source.description is not None
            assert public_file_for_public_contained_source.description in actual
            assert (
                public_file_for_public_citation_for_public_contained_source.description
                is not None
            )
            assert (
                public_file_for_public_citation_for_public_contained_source.description
                in actual
            )
            assert public_fact_for_public_citation_name in actual
            assert (
                public_fact_for_public_citation_for_public_contained_source_name
                in actual
            )

            assert private_file.description is not None
            assert private_file.description not in actual
            assert private_file_for_public_citation.description is not None
            assert private_file_for_public_citation.description not in actual
            assert public_file_for_private_citation.description is not None
            assert public_file_for_private_citation.description not in actual
            assert private_file_for_private_citation.description is not None
            assert private_file_for_private_citation.description not in actual
            assert private_file_for_public_contained_source.description is not None
            assert private_file_for_public_contained_source.description not in actual
            assert public_file_for_private_contained_source.description is not None
            assert public_file_for_private_contained_source.description not in actual
            assert private_file_for_private_contained_source.description is not None
            assert private_file_for_private_contained_source.description not in actual
            assert (
                private_file_for_public_citation_for_public_contained_source.description
                is not None
            )
            assert (
                private_file_for_public_citation_for_public_contained_source.description
                not in actual
            )
            assert (
                public_file_for_private_citation_for_public_contained_source.description
                is not None
            )
            assert (
                public_file_for_private_citation_for_public_contained_source.description
                not in actual
            )
            assert (
                private_file_for_private_citation_for_public_contained_source.description
                is not None
            )
            assert (
                private_file_for_private_citation_for_public_contained_source.description
                not in actual
            )
            assert (
                public_file_for_public_citation_for_private_contained_source.description
                is not None
            )
            assert (
                public_file_for_public_citation_for_private_contained_source.description
                not in actual
            )
            assert (
                private_file_for_public_citation_for_private_contained_source.description
                is not None
            )
            assert (
                private_file_for_public_citation_for_private_contained_source.description
                not in actual
            )
            assert (
                public_file_for_private_citation_for_private_contained_source.description
                is not None
            )
            assert (
                public_file_for_private_citation_for_private_contained_source.description
                not in actual
            )
            assert (
                private_file_for_private_citation_for_private_contained_source.description
                is not None
            )
            assert (
                private_file_for_private_citation_for_private_contained_source.description
                not in actual
            )
            assert private_fact_for_public_citation_name not in actual
            assert public_fact_for_private_citation_name not in actual
            assert private_fact_for_private_citation_name not in actual
            assert (
                private_fact_for_public_citation_for_public_contained_source_name
                not in actual
            )
            assert (
                public_fact_for_private_citation_for_public_contained_source_name
                not in actual
            )
            assert (
                private_fact_for_private_citation_for_public_contained_source_name
                not in actual
            )
            assert (
                public_fact_for_public_citation_for_private_contained_source_name
                not in actual
            )
            assert (
                private_fact_for_public_citation_for_private_contained_source_name
                not in actual
            )
            assert (
                public_fact_for_private_citation_for_private_contained_source_name
                not in actual
            )
            assert (
                private_fact_for_private_citation_for_private_contained_source_name
                not in actual
            )
