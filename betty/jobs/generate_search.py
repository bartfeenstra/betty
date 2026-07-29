"""
Search functionality jobs.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Final, final, override

from betty.job import Context, Job
from betty.localizables.gettext import _
from betty.localizables.markup import Chain
from betty.localizables.plain import Plain

if TYPE_CHECKING:
    from babel import Locale

    from betty.job.scheduler import Scheduler
    from betty.localizable import Localizable
    from betty.project import Project


@final
class GenerateSearch(Job):
    """
    Generate the search functionality.
    """

    # @todo Extract the HTML into a template
    _result_container_template: Final[Localizable] = Plain("""
    <li class="d-flex gap-2 search-result">
        {{{ betty-search-result }}}
    </li>
    """)

    # @todo Extract the HTML into a template
    _results_container_template: Final[Localizable] = Chain(
        '<ul class="entity-list"><h3 class="h2">',
        _("Results ({{{ betty-search-results-count }}})"),
        "</h3>{{{ betty-search-results }}}</ul>",
    )

    def __init__(self, *, project: Project):
        super().__init__("generate-search")
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await self._generate_search_index(
            self._result_container_template,
            self._results_container_template,
            scheduler.context,
        )

    async def _generate_search_index(
        self,
        result_container_template: Localizable,
        results_container_template: Localizable,
        context: Context,
    ) -> None:
        await gather(
            *(
                self._generate_search_index_for_locale(
                    result_container_template,
                    results_container_template,
                    locale,
                    context,
                )
                for locale in self._project.locales.keys()  # noqa: SIM118
            )
        )

    async def _generate_search_index_for_locale(
        self,
        result_container_template: Localizable,
        results_container_template: Localizable,
        locale: Locale,
        context: Context,
    ) -> None:
        raise NotImplementedError
        # localizer = await self._project.localizers.get(locale)
        # search_index = {
        #     "resultContainerTemplate": result_container_template.localize(localizer),
        #     "resultsContainerTemplate": results_container_template.localize(localizer),
        #     "index": [
        #         {
        #             "type": entry.id.id,
        #             "text": " ".join(entry.text),
        #             "result": entry.result,
        #         }
        #         for entry in await self._project.search.build(
        #             context=context, localizer=localizer
        #         )
        #     ],
        # }
        # search_index_json = json.dumps(search_index)
        # www_directory = self._project.localize_www_directory(locale)
        # await to_thread(www_directory.mkdir, exist_ok=True, parents=True)
        # await write(www_directory / "search-index.json", search_index_json)
