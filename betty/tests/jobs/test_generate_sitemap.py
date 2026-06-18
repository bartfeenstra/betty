from pathlib import Path

from lxml import etree

from betty.jobs.generate_sitemap import GenerateSitemap
from betty.project import Project
from betty.test_utils.job import do


class TestGenerateSitemap:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateSitemap(project=isolated_project))

        schema_doc = etree.parse(
            Path(__file__).parent / "test_generate_sitemap_assets" / "sitemap.xsd"
        )
        schema = etree.XMLSchema(schema_doc)
        sitemap_doc = etree.parse(isolated_project.www_directory / "sitemap.xml")
        schema.validate(sitemap_doc)
