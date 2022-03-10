class Acquirer:
    def acquire(self) -> None:
        raise NotImplementedError


class Releaser:
    def release(self) -> None:
        raise NotImplementedError
