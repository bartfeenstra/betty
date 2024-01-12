from __future__ import annotations

from betty.app.extension import Extension
from betty.extension.npm import _Npm


class _Webpack(Extension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_Npm}
