import json as stdjson
from pathlib import Path

import jsonschema
import pytest

from betty.app import App
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.openapi import Specification


class TestSpecification:
    @pytest.mark.parametrize('content_negotiation', [
        True,
        False,
    ])
    def test_build(self, content_negotiation: bool):
        with open(Path(__file__).parent / 'test_openapi_assets' / 'openapi-schema.json') as f:
            schema = stdjson.load(f)
        app = App()
        app.project.configuration.content_negotiation = content_negotiation
        sut = Specification(app)
        specification = sut.build()
        jsonschema.validate(specification, schema)

    def test_json_schema(self):
        with open(ASSETS_DIRECTORY_PATH / 'public' / 'static' / 'schema.json') as f:
            betty_json_schema = stdjson.load(f)
        with open(Path(__file__).parent / 'test_openapi_assets' / 'json-schema-schema.json') as f:
            json_schema_schema = stdjson.load(f)
        jsonschema.validate(betty_json_schema, json_schema_schema)
