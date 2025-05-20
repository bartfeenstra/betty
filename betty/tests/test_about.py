from betty import about
from betty.locale.localizer import DEFAULT_LOCALIZER


def test_report() -> None:
    assert len(about.report(localizer=DEFAULT_LOCALIZER).split("\n"))
