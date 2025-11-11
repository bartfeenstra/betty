from betty.locale.localize import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint.config.default import regional_content


def test_regional_content() -> None:
    actual = regional_content(localizers=[DEFAULT_LOCALIZER])
    assert actual
    for region, region_content in actual.items():
        assert region
        assert region_content
