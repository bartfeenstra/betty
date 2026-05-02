import pytest
from jsonschema import ValidationError

from betty.json_schema import JSON_SCHEMA
from betty.json_schema.validate import validate


def test_validate__with_invalid_data() -> None:
    with pytest.raises(ValidationError):
        validate(JSON_SCHEMA, None)


def test_validate__with_valid_data() -> None:
    validate(JSON_SCHEMA, {})
