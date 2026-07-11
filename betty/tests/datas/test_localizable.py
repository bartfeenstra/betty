from typing import TYPE_CHECKING, override

import pytest
from jsonschema import ValidationError

from betty.datas.localizable import (
    CountableLocalizableDefinition,
    LocalizableDefinition,
)
from betty.exception import HumanFacingException
from betty.linked_data import LinkedData
from betty.locale import default_locale_tag
from betty.locale.error import UnknownLocale
from betty.localizable import CountableLocalizable, Localizable, LocalizableCount
from betty.localizables.markup import Paragraph
from betty.localizables.plain import Plain
from betty.localizables.static import (
    CountableStaticTranslations,
    InvalidPluralTag,
    MissingPluralTag,
    StaticTranslations,
)
from betty.localizer import default_localizer
from betty.portable import PortableData
from betty.portable.error import NotPortable
from betty.project import Project
from betty.test_utils.linked_data import validate
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from betty.localizable import (
        ShorthandStaticTranslations,
    )


class TestLocalizableDefinition:
    def test_porter_load__without_translations_should_error(self) -> None:
        with pytest.raises(HumanFacingException):
            LocalizableDefinition().porter.load({})

    def test_porter_load__with_single_undetermined_translation(self) -> None:
        localizable = "Hello, world!"
        assert (
            LocalizableDefinition().porter.load(localizable).localize(default_localizer)
            == localizable
        )

    def test_porter_dump__with_plain_text(self) -> None:
        localizable = "Hello, world!"
        assert LocalizableDefinition().porter.dump(Plain(localizable)) == localizable

    def test_porter_dump__with_static_translations_single_undetermined(self) -> None:
        localizable = "Hello, world!"
        assert (
            LocalizableDefinition().porter.dump(StaticTranslations(localizable))
            == localizable
        )

    def test_porter_dump__with_static_translations(self) -> None:
        localizable: ShorthandStaticTranslations = {
            default_locale_tag: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }

        assert (
            LocalizableDefinition().porter.dump(StaticTranslations(localizable))
            == localizable
        )

    def test_porter_dump__with_unsupported_localizable(self) -> None:
        with pytest.raises(NotPortable):
            LocalizableDefinition().porter.dump(Paragraph("Hello, world!"))

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
    async def new_static_translations_schema__with_invalid_data(
        self, data: PortableData, isolated_project: Project
    ) -> None:
        with pytest.raises(ValidationError):
            validate(
                await LocalizableDefinition().linked_data_porter.schema(
                    isolated_project
                ),
                LinkedData(data),
            )

    @pytest.mark.parametrize(
        "data",
        [
            {default_locale_tag: "Hello, world!"},
            {"nl": "Hallo, wereld!", "uk": "Привіт Світ!"},
        ],
    )
    async def new_static_translations_schema__with_valid_data(
        self, data: PortableData, isolated_project: Project
    ) -> None:
        validate(
            await LocalizableDefinition().linked_data_porter.schema(isolated_project),
            LinkedData(data),
        )


class _NotDumpableCountableLocalizable(CountableLocalizable):
    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return DUMMY_LOCALIZABLE


class TestCountableLocalizableDefinition:
    def test_porter_load_countable_localizable(self) -> None:
        loaded = CountableLocalizableDefinition().porter.load({
            default_locale_tag: {
                "one": "{count} thing",
                "other": "{count} things",
            },
        })
        assert loaded.count(1).localize(default_localizer) == "1 thing"

    def test_porter_load_countable_localizable__without_locales(self) -> None:
        with pytest.raises(HumanFacingException):
            CountableLocalizableDefinition().porter.load({})

    def test_porter_load_countable_localizable__with_unknown_locale(self) -> None:
        with pytest.raises(UnknownLocale):
            CountableLocalizableDefinition().porter.load({
                "unknownlocale": {},
            })

    def test_porter_load_countable_localizable__with_missing_plural_tag(self) -> None:
        with pytest.raises(MissingPluralTag):
            CountableLocalizableDefinition().porter.load({
                default_locale_tag: {},
            })

    def test_porter_load_countable_localizable__wth_invalid_plural_tag(self) -> None:
        with pytest.raises(InvalidPluralTag):
            CountableLocalizableDefinition().porter.load({
                default_locale_tag: {
                    "one": "{count}",
                    "other": "{count}",
                    "invalid": "{count}",
                },
            })

    def test_porter_dump_countable_localizable(self) -> None:
        assert CountableLocalizableDefinition().porter.dump(
            CountableStaticTranslations({
                default_locale_tag: {
                    "one": "{count} thing",
                    "other": "{count} things",
                }
            })
        ) == {
            default_locale_tag: {
                "one": "{count} thing",
                "other": "{count} things",
            }
        }

    def test_porter_dump_countable_localizable__with_unsupported_localizable(
        self,
    ) -> None:
        with pytest.raises(NotPortable):
            CountableLocalizableDefinition().porter.dump(
                _NotDumpableCountableLocalizable()
            )
