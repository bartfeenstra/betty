from __future__ import annotations

from betty.datas.copyright_notice_definition import CopyrightNoticeDefinitionData
from betty.locale.localizable.plain import Plain
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestCopyrightNoticeDefinitionData:
    def test_summary(self) -> None:
        summary = Plain("My First Summary")
        sut = CopyrightNoticeDefinitionData(
            id="-dummy",
            label=DUMMY_LOCALIZABLE,
            summary=summary,
            text=DUMMY_LOCALIZABLE,
        )
        assert sut.summary is summary

    def test_text(self) -> None:
        text = Plain("My First Summary")
        sut = CopyrightNoticeDefinitionData(
            id="-dummy", label=DUMMY_LOCALIZABLE, summary=DUMMY_LOCALIZABLE, text=text
        )
        assert sut.text is text

    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-copyright-notice"
        label = Plain("-")
        summary = Plain("-")
        text = Plain("-")
        sut = CopyrightNoticeDefinitionData(
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
        sut = CopyrightNoticeDefinitionData(
            id="my-first-copyright-notice",
            label=DUMMY_LOCALIZABLE,
            description=description,
            summary=DUMMY_LOCALIZABLE,
            text=DUMMY_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description
