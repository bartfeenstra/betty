from typing import List


class CssProvider:
    @property
    def public_css_paths(self) -> List[str]:
        raise NotImplementedError(repr(self))


class JsProvider:
    @property
    def public_js_paths(self) -> List[str]:
        raise NotImplementedError(repr(self))
