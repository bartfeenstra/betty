from __future__ import annotations

from betty.datas.license_definition import LicenseDefinitionData
from betty.localizables.plain import Plain


class TestLicenseDefinitionData:
    def test_summary(self) -> None:
        summary = Plain("My First Summary")
        sut = LicenseDefinitionData(
            id="-dummy",
            label="-",
            summary=summary,
            text="-",
        )
        assert sut.summary is summary

    def test_text(self) -> None:
        text = Plain("My First Summary")
        sut = LicenseDefinitionData(id="-dummy", label="-", summary="-", text=text)
        assert sut.text is text

    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-license"
        label = Plain("-")
        summary = Plain("-")
        text = Plain("-")
        sut = LicenseDefinitionData(
            id=plugin_id,
            label=label,
            summary=summary,
            text=text,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.cls().summary is summary
        assert plugin.cls().text is text

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        sut = LicenseDefinitionData(
            id="my-first-license",
            label="-",
            description=description,
            summary="-",
            text="-",
        )
        plugin = sut.new_plugin()
        assert plugin.description is description
