from typing import Set


class HtmlProvider:
    @property
    def public_css_paths(self) -> Set[str]:
        return set()

    @property
    def public_js_paths(self) -> Set[str]:
        return set()
