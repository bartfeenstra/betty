"""
Webpack-related document variables.
"""

from __future__ import annotations

from typing import final, override

from betty.document import DocumentProvider, DocumentProviderDefinition, DocumentVars


@final
@DocumentProviderDefinition("webpack")
class Webpack(DocumentProvider):
    """
    .. plugin:: document-provider:webpack.
    """

    @override
    def new_document_vars(self) -> DocumentVars:
        return {
            "webpack_js_entry_points": set(),
        }
