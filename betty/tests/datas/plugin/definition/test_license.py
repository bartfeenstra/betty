from __future__ import annotations

from betty.datas.plugin.definition.license import LicenseDefinitionData


class TestLicenseDefinitionData:
    def test_summary(self) -> None:
        summary = "My First Summary"
        sut = LicenseDefinitionData(
            id="-dummy",
            label="-",
            summary=summary,
            text="-",
        )
        assert sut.summary == summary

    def test_text(self) -> None:
        text = "My First Text"
        sut = LicenseDefinitionData(id="-dummy", label="-", summary="-", text=text)
        assert sut.text == text

    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-license"
        label = "My First Label"
        summary = "My First Summary"
        text = "My First Text"
        sut = LicenseDefinitionData(
            id=plugin_id,
            label=label,
            summary=summary,
            text=text,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label == label
        assert plugin.cls().summary == summary
        assert plugin.cls().text == text

    def test_new_plugin__full(self) -> None:
        description = "My First Description"
        sut = LicenseDefinitionData(
            id="my-first-license",
            label="-",
            description=description,
            summary="-",
            text="-",
        )
        plugin = sut.new_plugin()
        assert plugin.description == description
