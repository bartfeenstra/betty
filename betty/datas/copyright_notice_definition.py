"""
Copyright notice definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.human_facing_plugin_definition import HumanFacingPluginDefinitionData
from betty.locale.localizable.gettext import _
from betty.properties.localizable import LocalizableProperty
from betty.sample import Sample

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable, ResolvableLocalizable


@final
@ObjectDefinition(
    label=_("Copyright notice configuration"),
    samples=[
        lambda: Sample(
            CopyrightNoticeDefinitionData(
                id="my-first-copyright-notice",
                label="My First Copyright Notice",
                summary="My First Copyright Notice is my first copyright notice",
                text="My First Copyright Notice is my first copyright notice, all rights are reserved.",
            ),
            label="Default",
        )
    ],
)
class CopyrightNoticeDefinitionData(
    HumanFacingPluginDefinitionData[CopyrightNoticeDefinition]
):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticeDefinition`.

    .. data:: betty.datas.copyright_notice_definition:CopyrightNoticeDefinitionData
    """

    summary = LocalizableProperty(label=_("Summary"))
    text = LocalizableProperty(label=_("Text"))

    def __init__(
        self,
        *,
        summary: ResolvableLocalizable,
        text: ResolvableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.summary = summary
        self.text = text

    @override
    def new_plugin(self) -> CopyrightNoticeDefinition:
        configuration = self

        @CopyrightNoticeDefinition(
            self.id,
            label=self.label,
            description=self.description,
        )
        class _CopyrightNoticeDefinitionDataCopyrightNotice(CopyrightNotice):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _CopyrightNoticeDefinitionDataCopyrightNotice.plugin()
