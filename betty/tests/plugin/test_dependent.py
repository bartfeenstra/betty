from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.plugin.collections import new_plugin_definitions
from betty.plugin.dependent import (
    DependentPluginDefinition,
    expand_plugin_dependencies,
    sort_dependent_plugin_graph,
)
from betty.tests.plugin.test___init__ import (
    _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
    _DEPENDENT_PLUGIN_ISOLATED,
    _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
    _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
    _DependentPluginDefinition,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.machine_name import MachineName


class TestDependentPluginDefinition:
    def test_depends_on(self) -> None:
        depends_on = {"depends-on"}
        sut = DependentPluginDefinition(
            "my-first-plugin",
            depends_on=depends_on,
        )
        assert sut.depends_on == depends_on

    def test_comes_after(self) -> None:
        depends_on = {"depends-on"}
        sut = DependentPluginDefinition("my-first-plugin", depends_on=depends_on)
        assert sut.comes_after == depends_on


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            set(),
            set(),
        ),
        (
            {
                _DEPENDENT_PLUGIN_ISOLATED,
            },
            {
                _DEPENDENT_PLUGIN_ISOLATED,
            },
        ),
        (
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
        ),
        (
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            {_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT},
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
    ],
)
async def test_expand_plugin_dependencies(
    expected: set[_DependentPluginDefinition],
    plugins: set[_DependentPluginDefinition],
) -> None:
    actual = await expand_plugin_dependencies(
        new_plugin_definitions(
            _DEPENDENT_PLUGIN_ISOLATED,
            _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
            _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
        ),
        plugins,
    )
    assert actual == expected


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            [],
            set(),
        ),
        (
            [
                _DEPENDENT_PLUGIN_ISOLATED.id,
            ],
            {
                _DEPENDENT_PLUGIN_ISOLATED,
            },
        ),
        (
            [
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT.id,
            ],
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            [
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT.id,
            ],
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
        ),
        (
            [
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT.id,
            ],
            {
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            [_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id],
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
    ],
)
async def test_sort_dependent_plugin_graph(
    expected: list[MachineName], plugins: Iterable[_DependentPluginDefinition]
) -> None:
    plugin_repository = new_plugin_definitions(
        _DEPENDENT_PLUGIN_ISOLATED,
        _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
        _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
        _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
    )
    sorter = await sort_dependent_plugin_graph(plugin_repository, plugins)
    assert list(sorter.static_order()) == expected
