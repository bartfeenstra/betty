from betty.entity import EntityDefinition
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE


class TestEntityDefinition:
    def test_public_facing(self) -> None:
        sut = EntityDefinition(
            "-dummy",
            public_facing=True,
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.public_facing
