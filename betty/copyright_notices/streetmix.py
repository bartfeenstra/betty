"""
The Streetmix copyright notice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.freezers.classtools import FrozenOnInit

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


@final
@CopyrightNoticeDefinition("streetmix", label="Streetmix LLC")
class Streetmix(CopyrightNotice, FrozenOnInit):
    """
    .. plugin:: copyright-notice:streetmix.
    """

    @override
    @property
    def summary(self) -> AnyLocalizable:
        return self.definition.label

    @override
    @property
    def text(self) -> AnyLocalizable:
        return self.definition.label

    @override
    @property
    def url(self) -> AnyLocalizable:
        return "https://github.com/streetmix/streetmix"
