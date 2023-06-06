from contextlib import suppress
from typing import Any, cast

from typing_extensions import TypeAlias

from betty.app import App
from betty.serde.dump import DictDump, Dump

Schema: TypeAlias = DictDump[Dump]


class Describable:
    @classmethod
    def schema(cls, app: App) -> Schema:
        return {}


def object_schema(schema: Any = None) -> Schema:
    if schema is not None:
        assert isinstance(schema, dict)
        with suppress(KeyError):
            assert 'object' == schema['type']
        with suppress(KeyError):
            assert isinstance(schema['properties'], list)
    else:
        schema = {}
    schema['type'] = 'object'
    schema['properties'] = []
    schema['required'] = []
    return cast(Schema, schema)
