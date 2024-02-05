"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, overload, Any

from betty.serde.dump import DictDump, Dump, ListDump

if TYPE_CHECKING:
    from betty.app import App
    from betty.model.ancestry import Link


class LinkedDataDumpable:
    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """
        return {}


@overload
def dump_default(dump: DictDump[Dump], key: str, default_type: type[dict[Any, Any]]) -> DictDump[Dump]:
    pass


@overload
def dump_default(dump: DictDump[Dump], key: str, default_type: type[list[Any]]) -> ListDump[Dump]:
    pass


def dump_default(dump, key, default_type):
    """
    Add a key and value to a dump, if the key does not exist yet.
    """
    try:
        assert isinstance(dump[key], default_type)
    except KeyError:
        dump[key] = default_type()
    return dump[key]  # type: ignore[return-value]


def dump_context(dump: DictDump[Dump], **contexts: str | Sequence[str]) -> None:
    """
    Add one or more contexts to a dump.
    """
    context_dump = dump_default(dump, '@context', dict)
    for key, schema_org in contexts.items():
        context_dump[key] = f'https://schema.org/{schema_org}'


async def dump_link(dump: DictDump[Dump], app: App, *links: Link) -> None:
    """
    Add one or more links to a dump.
    """
    link_dump = dump_default(dump, 'links', list)
    for link in links:
        link_dump.append(await link.dump_linked_data(app))
