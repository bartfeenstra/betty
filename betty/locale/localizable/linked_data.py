"""
Linked data for the localizable API.
"""

from collections.abc import Iterable

from betty.locale.localizable import Localizable, StaticTranslations
from betty.locale.localizer import Localizer
from betty.serde.dump import Dump, DumpMapping


def dump_linked_data(
    localizable: Localizable, *, localizers: Iterable[Localizer]
) -> DumpMapping[Dump]:
    """
    Dump a :py:class:`betty.locale.localizable.Localizable` to `JSON-LD <https://json-ld.org/>`_.
    """
    return {**StaticTranslations.from_localizable(localizable, localizers).translations}
