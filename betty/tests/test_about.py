from betty import about
from betty.locale.localizer import DEFAULT_LOCALIZER


async def test_version() -> None:
    assert about.version()


async def test_version_label() -> None:
    assert about.version_label()


def test_is_development() -> None:
    assert about.is_development()


def test_is_stable() -> None:
    assert not about.is_stable()


def test_report() -> None:
    assert len(about.report(localizer=DEFAULT_LOCALIZER).split("\n"))
