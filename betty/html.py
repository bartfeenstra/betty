from typing import Set


class HtmlProvider:
    @property
    def css_paths(self) -> Set[str]:
        return set()

    @property
    def js_paths(self) -> Set[str]:
        return set()
