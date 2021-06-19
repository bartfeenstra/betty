import json as stdjson
from pathlib import Path
from tempfile import TemporaryDirectory

import jsonschema
from parameterized import parameterized

from betty.config import Configuration
from betty.asyncio import sync
from betty.openapi import build_specification
from betty.app import App
from betty.tests import TestCase


class BuildSpecificationTest(TestCase):
    @parameterized.expand([
        (True,),
        (False,),
    ])
    @sync
    async def test(self, content_negotiation: str):
        with open(Path(__file__).parent / 'test_openapi_assets' / 'schema.json') as f:
            schema = stdjson.load(f)
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.content_negotiation = content_negotiation
            async with App(configuration) as app:
                specification = build_specification(app)
        jsonschema.validate(specification, schema)
