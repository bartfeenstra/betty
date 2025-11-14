from typing import TYPE_CHECKING

import pytest

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import (
    LocalizableLike,
    Paragraph,
    Plain,
    StaticTranslations,
)
from betty.locale.localizable.config import (
    LocalizableConfiguration,
    OptionalLocalizableConfigurationAttr,
    RequiredLocalizableConfigurationAttr,
    RequiredLocalizableConfigurationAttrNotInitialized,
)
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.serde.dump import NotDumpable

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestLocalizableConfiguration:
    async def test_localizable(self) -> None:
        localizable_one = Plain("")
        sut = LocalizableConfiguration(localizable_one)
        assert sut.localizable is localizable_one
        localizable_two = Plain("")
        sut.localizable = localizable_two
        assert sut.localizable is localizable_two

    async def test_load__without_translations_should_error(self) -> None:
        sut = LocalizableConfiguration("")
        with pytest.raises(HumanFacingException):
            sut.load({})

    async def test_load__with_single_undetermined_translation(self) -> None:
        localizable = "Hello, world!"
        sut = LocalizableConfiguration("")
        dump: Dump = localizable
        sut.load(dump)
        assert sut.localizable.localize(DEFAULT_LOCALIZER) == localizable

    async def test_dump__with_plain_text(self) -> None:
        localizable = "Hello, world!"
        sut = LocalizableConfiguration(localizable)
        assert sut.dump() == localizable

    async def test_dump__with_static_translations_single_undetermined(self) -> None:
        localizable = "Hello, world!"
        sut = LocalizableConfiguration(StaticTranslations(localizable))
        assert sut.dump() == localizable

    async def test_dump__with_static_translations(self) -> None:
        localizable = {
            DEFAULT_LOCALE: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }
        sut = LocalizableConfiguration(localizable)
        assert sut.dump() == localizable

    async def test_dump__with_unsupported_localizable(self) -> None:
        localizable = Paragraph("Hello, world!")
        sut = LocalizableConfiguration(localizable)
        with pytest.raises(NotDumpable):
            sut.dump()


class TestRequiredLocalizableConfigurationAttr:
    class _Instance:
        attr = RequiredLocalizableConfigurationAttr("attr")

        def __init__(self, attr: LocalizableLike):
            self.attr = attr

    def test___get__(self) -> None:
        localizable = Plain("")
        instance = self._Instance(localizable)
        assert instance.attr is localizable

    def test___get___not_initialized(self) -> None:
        class _Instance:
            attr = RequiredLocalizableConfigurationAttr("attr")

        instance = _Instance()
        with pytest.raises(RequiredLocalizableConfigurationAttrNotInitialized):
            instance.attr  # noqa B018

    def test___set__(self) -> None:
        instance = self._Instance("")
        translation = "Hello, world!"
        instance.attr = translation
        assert instance.attr.localize(DEFAULT_LOCALIZER) == translation

    def test_dump(self) -> None:
        localizable = "Hello, world!"
        instance = self._Instance(localizable)
        assert self._Instance.attr.dump(instance) == localizable


class TestOptionalLocalizableConfigurationAttr:
    class _Instance:
        attr = OptionalLocalizableConfigurationAttr("attr")

        def __init__(self, attr: LocalizableLike | None = None):
            if attr is not None:
                self.attr = attr

    def test___get___without_localizable(self) -> None:
        instance = self._Instance()
        assert instance.attr is None

    def test___get___with_localizable(self) -> None:
        localizable = Plain("")
        instance = self._Instance(localizable)
        assert instance.attr is localizable

    def test___set__(self) -> None:
        translation = "Hello, world!"
        instance = self._Instance()
        instance.attr = translation
        assert instance.attr is not None
        assert instance.attr.localize(DEFAULT_LOCALIZER) == translation

    def test___delete__(self) -> None:
        instance = self._Instance("Hello, world!")
        del instance.attr
        assert instance.attr is None

    def test_dump__without_localizable(self) -> None:
        instance = self._Instance()
        assert self._Instance.attr.dump(instance) is None

    def test_dump__with_localizable(self) -> None:
        localizable = "Hello, world!"
        instance = self._Instance(localizable)
        assert self._Instance.attr.dump(instance) == localizable
