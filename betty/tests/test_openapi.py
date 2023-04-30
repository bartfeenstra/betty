import json as stdjson
from pathlib import Path

import jsonschema
import pytest

from betty.app import App
from betty.openapi import Specification


class TestSpecification:
    @pytest.mark.parametrize('content_negotiation', [
        True,
        False,
    ])
    def test_build(self, content_negotiation: bool):
        with open(Path(__file__).parent / 'test_openapi_assets' / 'schema.json') as f:
            schema = stdjson.load(f)
        app = App()
        app.project.configuration.content_negotiation = content_negotiation
        sut = Specification(app)
        specification = sut.build()
        jsonschema.validate(specification, schema)
