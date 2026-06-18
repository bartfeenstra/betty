from unittest.mock import AsyncMock

from betty.gramps.loader import GrampsLoader
from betty.jobs.load_gramps_ancestry import LoadGrampsAncestry
from betty.test_utils.job import do


class TestLoadGrampsAncestry:
    async def test_do(self) -> None:
        m_gramps_loader = AsyncMock(spec=GrampsLoader)
        family_tree_name = "my-first-family-tree"
        await do(
            LoadGrampsAncestry(loader=m_gramps_loader, source=family_tree_name),
        )
        m_gramps_loader.load_name.assert_awaited_once_with(family_tree_name)
