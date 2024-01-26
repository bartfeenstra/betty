"""
Provide JSON utilities.
"""
from __future__ import annotations

import json as stdjson
from os import path
from typing import Any, TypeVar

import jsonschema
from jsonschema import RefResolver

from betty.app import App

T = TypeVar('T')


def validate(data: Any, schema_definition: str, app: App) -> None:
    """
    Validate JSON against the Betty JSON schema.
    """
    with open(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'schema.json'), encoding='utf-8') as f:
        json_data = f.read()
    schema = stdjson.loads(json_data)
    # @todo Can we set the schema ID somehow without making the entire JSON schema file a Jinja2 template?
    schema_id = app.static_url_generator.generate('schema.json', absolute=True)
    schema['$id'] = schema_id
    ref_resolver = RefResolver(schema_id, schema)
    jsonschema.validate(
        data, schema['definitions'][schema_definition], resolver=ref_resolver)
