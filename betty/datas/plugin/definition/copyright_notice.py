"""
Copyright notice definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.localizable import new_localizable_attr
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.datas.definition.human_facing import HumanFacingDefinitionConfig
from betty.datas.plugin.definition import (
    PluginDefinitionConfig,
    PluginDefinitionConfigDefinition,
)
from betty.localizables.gettext import _
from betty.sample import Sample, Samples

if TYPE_CHECKING:
    from betty.localizable import Localizable, ResolvableLocalizable


@final
@PluginDefinitionConfigDefinition(
    CopyrightNoticeDefinition,
    samples=Samples(
        lambda: Sample(
            CopyrightNoticeDefinitionConfig(
                id="my-first-copyright-notice",
                label="My First Copyright Notice",
                summary="My First Copyright Notice is my first copyright notice",
                text="My First Copyright Notice is my first copyright notice, all rights are reserved.",
            ),
            label="Default",
        )
    ),
)
class CopyrightNoticeDefinitionConfig(
    HumanFacingDefinitionConfig[CopyrightNoticeDefinition],
    PluginDefinitionConfig[CopyrightNoticeDefinition],
):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticeDefinition`.

    .. data:: betty.datas.copyright_notice_definition:CopyrightNoticeDefinitionConfig
    """

    summary = new_localizable_attr(label=_("Summary"))
    text = new_localizable_attr(label=_("Text"))

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
    def new_definition(self) -> CopyrightNoticeDefinition:
        configuration = self

        @CopyrightNoticeDefinition(
            self.id,
            label=self.label,
            description=self.description,
        )
        class _CopyrightNoticeDefinitionConfigCopyrightNotice(CopyrightNotice):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _CopyrightNoticeDefinitionConfigCopyrightNotice.definition
