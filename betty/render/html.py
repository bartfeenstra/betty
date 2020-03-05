from collections import Iterable


class HtmlProvider:
    @property
    def css_paths(self) -> Iterable[str]:
        return []

    @property
    def js_paths(self) -> Iterable[str]:
        return []
