import json as stdjson
from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase

import jsonschema
from parameterized import parameterized

from betty.config import Configuration
from betty.openapi import build_specification
from betty.site import Site


class BuildSpecificationTest(TestCase):
    @parameterized.expand([
        (True,),
        (False,),
    ])
    def test(self, content_negotiation: str):
        with open(path.join(path.dirname(__file__), 'resources', 'openapi', 'schema.json')) as f:
            schema = stdjson.load(f)
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.content_negotiation = content_negotiation
            with Site(configuration) as site:
                specification = build_specification(site)
        jsonschema.validate(specification, schema)
