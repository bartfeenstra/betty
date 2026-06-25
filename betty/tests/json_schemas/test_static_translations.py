import pytest
from jsonschema.exceptions import ValidationError

from betty.json_schema import validate
from betty.json_schemas.static_translations import new_static_translations_schema
from betty.locale import default_locale_tag
from betty.portable import PortableData


@pytest.mark.parametrize(
    "data",
    [
        True,
        False,
        None,
        123,
        [],
        {default_locale_tag: True},
        {default_locale_tag: False},
        {default_locale_tag: None},
        {default_locale_tag: 123},
        {default_locale_tag: []},
        {default_locale_tag: {}},
    ],
)
def new_static_translations_schema__with_invalid_data(data: PortableData) -> None:
    with pytest.raises(ValidationError):
        validate(new_static_translations_schema(), data)


@pytest.mark.parametrize(
    "data",
    [
        {default_locale_tag: "Hello, world!"},
        {"nl": "Hallo, wereld!", "uk": "Привіт Світ!"},
    ],
)
def new_static_translations_schema__with_valid_data(data: PortableData) -> None:
    validate(new_static_translations_schema(), data)
