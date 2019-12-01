import json as stdjson
from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase

import jsonschema

from betty.config import Configuration
from betty.render import render
from betty.site import Site


class OpenApiTest(TestCase):
    def test_render(self):
        with open(path.join(path.dirname(__file__), 'resources', 'openapi', 'schema.json')) as f:
            schema = stdjson.load(f)
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            site = Site(configuration)
            render(site)
            with open(path.join(output_directory_path, 'www', 'api', 'index.json')) as f:
                specification = stdjson.load(f)
        jsonschema.validate(specification, schema)
