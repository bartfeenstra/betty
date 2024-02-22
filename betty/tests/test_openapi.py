import json as stdjson
from pathlib import Path

import aiofiles
import jsonschema
import pytest

from betty.app import App
from betty.openapi import Specification


class TestSpecification:
    @pytest.mark.parametrize('clean_urls', [
        True,
        False,
    ])
    async def test_build(self, clean_urls: bool) -> None:
        async with aiofiles.open(Path(__file__).parent / 'test_openapi_assets' / 'openapi-schema.json') as f:
            schema = stdjson.loads(await f.read())
        app = App()
        app.project.configuration.clean_urls = clean_urls
        sut = Specification(app)
        specification = await sut.build()
        jsonschema.validate(specification, schema)
