from __future__ import annotations

from typing import TYPE_CHECKING, Final, final, override

from betty.extensions._theme.search import generate_search_index
from betty.job import Job
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Chain
from betty.locale.localizable.plain import Plain

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.locale.localizable import Localizable
    from betty.project import Project


@final
class _GenerateRaspberryMintSearchIndex(Job):
    _result_container_template: Final[Localizable] = Plain("""
    <li class="d-flex gap-2 search-result">
        {{{ betty-search-result }}}
    </li>
    """)

    _results_container_template: Final[Localizable] = Chain(
        '<ul class="entity-list"><h3 class="h2">',
        _("Results ({{{ betty-search-results-count }}})"),
        "</h3>{{{ betty-search-results }}}</ul>",
    )

    def __init__(self, *, project: Project):
        super().__init__("raspberry-mint:generate-search-index")
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await generate_search_index(
            self._project,
            self._result_container_template,
            self._results_container_template,
            context=scheduler.context,
        )
