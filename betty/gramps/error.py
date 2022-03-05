from betty.error import UserFacingError


class GrampsError(UserFacingError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
