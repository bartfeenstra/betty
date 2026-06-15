from typing import TYPE_CHECKING

import pytest

from betty.datas.localizable import LocalizableDefinition
from betty.exception import HumanFacingException
from betty.locale import default_locale_tag
from betty.locale.localizable.markup import Paragraph
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import default_localizer
from betty.portable.error import NotPortable

if TYPE_CHECKING:
    from betty.locale.localizable import ShorthandStaticTranslations


class TestLocalizableDefinition:
    def test_load__without_translations_should_error(self) -> None:
        with pytest.raises(HumanFacingException):
            LocalizableDefinition().porter.load({})

    def test_load__with_single_undetermined_translation(self) -> None:
        localizable = "Hello, world!"
        assert (
            LocalizableDefinition().porter.load(localizable).localize(default_localizer)
            == localizable
        )

    def test_dump__with_plain_text(self) -> None:
        localizable = "Hello, world!"
        assert LocalizableDefinition().porter.dump(Plain(localizable)) == localizable

    def test_dump__with_static_translations_single_undetermined(self) -> None:
        localizable = "Hello, world!"
        assert (
            LocalizableDefinition().porter.dump(StaticTranslations(localizable))
            == localizable
        )

    def test_dump__with_static_translations(self) -> None:
        localizable: ShorthandStaticTranslations = {
            default_locale_tag: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }

        assert (
            LocalizableDefinition().porter.dump(StaticTranslations(localizable))
            == localizable
        )

    def test_dump__with_unsupported_localizable(self) -> None:
        with pytest.raises(NotPortable):
            LocalizableDefinition().porter.dump(Paragraph("Hello, world!"))
