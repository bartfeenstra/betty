from __future__ import annotations

from betty.datas.plugin.definition.copyright_notice import (
    CopyrightNoticeDefinitionConfig,
)


class TestCopyrightNoticeDefinitionConfig:
    def test_summary(self) -> None:
        summary = "My First Summary"
        sut = CopyrightNoticeDefinitionConfig(
            id="-dummy",
            label="-",
            summary=summary,
            text="-",
        )
        assert sut.summary == summary

    def test_text(self) -> None:
        text = "My First Text"
        sut = CopyrightNoticeDefinitionConfig(
            id="-dummy", label="-", summary="-", text=text
        )
        assert sut.text == text

    def test_new_definition__minimal(self) -> None:
        plugin_id = "my-first-copyright-notice"
        label = "My First Label"
        summary = "My First Summary"
        text = "My First Text"
        sut = CopyrightNoticeDefinitionConfig(
            id=plugin_id,
            label=label,
            summary=summary,
            text=text,
        )
        plugin = sut.new_definition()
        assert plugin.id == plugin_id
        assert plugin.label == label
        assert plugin.cls().summary == summary
        assert plugin.cls().text == text

    def test_new_definition__full(self) -> None:
        description = "My First Description"
        sut = CopyrightNoticeDefinitionConfig(
            id="my-first-copyright-notice",
            label="-",
            description=description,
            summary="-",
            text="-",
        )
        plugin = sut.new_definition()
        assert plugin.description == description
