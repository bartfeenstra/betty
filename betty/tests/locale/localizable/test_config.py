import pytest

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import Paragraph, Plain, StaticTranslations
from betty.locale.localizable.config import dump_localizable, load_localizable
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.serde.dump import NotDumpable


async def test_load_localizable__without_translations_should_error() -> None:
    with pytest.raises(HumanFacingException):
        load_localizable({})


async def test_load_localizable__with_single_undetermined_translation() -> None:
    localizable = "Hello, world!"
    assert load_localizable(localizable).localize(DEFAULT_LOCALIZER) == localizable


async def test_dump_localizable__with_plain_text() -> None:
    localizable = "Hello, world!"
    assert dump_localizable(Plain(localizable)) == localizable


async def test_dump_localizable__with_static_translations_single_undetermined() -> None:
    localizable = "Hello, world!"
    assert dump_localizable(StaticTranslations(localizable)) == localizable


async def test_dump_localizable__with_static_translations() -> None:
    localizable = {
        DEFAULT_LOCALE: "Hello, world!",
        "nl-NL": "Hallo, wereld!",
    }

    assert dump_localizable(StaticTranslations(localizable)) == localizable


async def test_dump_localizable__with_unsupported_localizable() -> None:
    with pytest.raises(NotDumpable):
        dump_localizable(Paragraph("Hello, world!"))
