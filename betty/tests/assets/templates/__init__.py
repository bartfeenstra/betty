from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.config import Configuration
from betty.site import Site


class TemplateTestCase(TestCase):
    @property
    def template(self) -> str:
        raise NotImplementedError

    async def _render(self, **data):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            configuration.mode = 'development'
            async with Site(configuration) as site:
                return await site.jinja2_environment.get_template(self.template).render_async(**data)
