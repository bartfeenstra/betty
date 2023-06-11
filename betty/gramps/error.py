from typing import Any

from betty.error import UserFacingError


class GrampsError(UserFacingError):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
