import json as stdjson
from pathlib import Path

import aiofiles
import jsonschema
import pytest

from betty.app import App
from betty.json.schema import Schema


class TestSchema:
    @pytest.mark.parametrize('clean_urls', [
        True,
        False,
    ])
    async def test_build(self, clean_urls: bool) -> None:
        async with aiofiles.open(Path(__file__).parent / 'test_schema_assets' / 'json-schema-schema.json') as f:
            json_schema_schema = stdjson.loads(await f.read())

        async with (App.new_temporary() as app, app):
            sut = Schema(app)
            schema = await sut.build()
        jsonschema.validate(json_schema_schema, schema)
