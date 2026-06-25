from betty.date import Date, DateRange
from betty.porters.date import AnyDatePorter


class TestAnyDatePorter:
    def test_load__with_date(self) -> None:
        assert isinstance(AnyDatePorter().load({}), Date)

    def test_load__with_date_range(self) -> None:
        assert isinstance(
            AnyDatePorter().load({"start": {}}),
            DateRange,
        )

    def test_dump__with_date(self) -> None:
        assert AnyDatePorter().dump(Date(1970, 1, 1)) == {
            "year": 1970,
            "month": 1,
            "day": 1,
        }

    def test_dump__with_date_range(self) -> None:
        assert AnyDatePorter().dump(DateRange(Date(1970, 1, 1), Date(2002, 2, 2))) == {
            "start": {
                "year": 1970,
                "month": 1,
                "day": 1,
            },
            "end": {
                "year": 2002,
                "month": 2,
                "day": 2,
            },
        }
