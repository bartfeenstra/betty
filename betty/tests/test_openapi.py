import json as stdjson
from pathlib import Path

import jsonschema
import pytest

from betty.app import App
from betty.openapi import build_specification


class TestBuildSpecification:
    @pytest.mark.parametrize('content_negotiation', [
        True,
        False,
    ])
    def test(self, content_negotiation: bool):
        with open(Path(__file__).parent / 'test_openapi_assets' / 'schema.json') as f:
            schema = stdjson.load(f)
            with App() as app:
                app.project.configuration.content_negotiation = content_negotiation
                specification = build_specification(app)
        jsonschema.validate(specification, schema)
