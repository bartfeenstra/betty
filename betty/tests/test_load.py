from betty.load import load
from betty.project import Project


async def test_load__should_freeze_ancestry(isolated_project: Project) -> None:
    assert not isolated_project.ancestry.is_frozen
    await load(isolated_project)
    assert isolated_project.ancestry.is_frozen
