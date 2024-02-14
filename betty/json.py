"""
Provide JSON utilities.
"""
from __future__ import annotations

import json as stdjson
from os import path
from typing import Any, TypeVar

from jsonschema.validators import Draft202012Validator
from referencing import Resource, Registry

from betty.app import App

T = TypeVar('T')


def validate(data: Any, app: App) -> None:
    """
    Validate JSON against the Betty JSON schema.
    """
    with open(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'schema.json'), encoding='utf-8') as f:
        json_data = f.read()
    schema_data = stdjson.loads(json_data)
    schema_id = app.static_url_generator.generate('schema.json', absolute=True)
    schema_data['$id'] = schema_id
    schema = Resource.from_contents(schema_data)
    schema_registry: Registry[Any] = schema @ Registry()
    validator = Draft202012Validator(
        {
            '$ref': data['$schema'],
        },
        registry=schema_registry,
    )
    validator.validate(data)
