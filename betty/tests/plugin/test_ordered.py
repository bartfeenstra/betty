from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.plugin.ordered import (
    OrderedPluginDefinition,
    get_comes_after,
    get_comes_before,
    sort_ordered_plugin_graph,
)
from betty.service.level import UNIVERSE
from betty.service.plugin import PluginManager
from betty.tests.plugin.test___init__ import (
    _ORDERED_PLUGIN_COMES_AFTER_TARGET,
    _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
    _ORDERED_PLUGIN_HAS_COMES_AFTER,
    _ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL,
    _ORDERED_PLUGIN_HAS_COMES_BEFORE,
    _ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL,
    _ORDERED_PLUGIN_ISOLATED,
    _OrderedPluginDefinition,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.machine_name import MachineName


class TestOrderedPluginDefinition:
    def test_comes_before(self) -> None:
        comes_before = {"comes-before"}
        sut = OrderedPluginDefinition("my-first-plugin", comes_before=comes_before)
        assert sut.comes_before == comes_before

    def test_comes_after(self) -> None:
        comes_after = {"comes-after"}
        sut = OrderedPluginDefinition("my-first-plugin", comes_after=comes_after)
        assert sut.comes_after == comes_after


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            [],
            [],
        ),
        (
            [_ORDERED_PLUGIN_ISOLATED.id],
            [_ORDERED_PLUGIN_ISOLATED],
        ),
        (
            [_ORDERED_PLUGIN_HAS_COMES_AFTER.id],
            [_ORDERED_PLUGIN_HAS_COMES_AFTER],
        ),
        (
            [
                _ORDERED_PLUGIN_COMES_AFTER_TARGET.id,
                _ORDERED_PLUGIN_HAS_COMES_AFTER.id,
            ],
            [
                _ORDERED_PLUGIN_COMES_AFTER_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_AFTER,
            ],
        ),
        (
            [_ORDERED_PLUGIN_HAS_COMES_BEFORE.id],
            [_ORDERED_PLUGIN_HAS_COMES_BEFORE],
        ),
        (
            [
                _ORDERED_PLUGIN_HAS_COMES_BEFORE.id,
                _ORDERED_PLUGIN_COMES_BEFORE_TARGET.id,
            ],
            [
                _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_BEFORE,
            ],
        ),
    ],
)
async def test_sort_ordered_plugin_graph(
    expected: list[MachineName],
    plugins: Iterable[_OrderedPluginDefinition],
) -> None:
    sorter = await sort_ordered_plugin_graph(
        PluginManager(
            UNIVERSE,
            _OrderedPluginDefinition,
            [
                _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_BEFORE,
                _ORDERED_PLUGIN_COMES_AFTER_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_AFTER,
                _ORDERED_PLUGIN_ISOLATED,
            ],
        ),
        plugins,
    )
    assert list(sorter.static_order()) == expected


@pytest.mark.parametrize(
    ("expected", "origin"),
    [
        (
            set(),
            _ORDERED_PLUGIN_ISOLATED,
        ),
        (
            {_ORDERED_PLUGIN_COMES_AFTER_TARGET},
            _ORDERED_PLUGIN_HAS_COMES_AFTER,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_BEFORE},
            _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL},
            _ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL,
        ),
    ],
)
async def test_get_comes_after(
    expected: set[_OrderedPluginDefinition], origin: _OrderedPluginDefinition
) -> None:
    assert (
        await get_comes_after(
            PluginManager(
                UNIVERSE,
                _OrderedPluginDefinition,
                [
                    _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
                    _ORDERED_PLUGIN_HAS_COMES_BEFORE,
                    _ORDERED_PLUGIN_COMES_AFTER_TARGET,
                    _ORDERED_PLUGIN_HAS_COMES_AFTER,
                    _ORDERED_PLUGIN_ISOLATED,
                    _ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL,
                    _ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL,
                ],
            ),
            origin,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("expected", "origin"),
    [
        (
            set(),
            _ORDERED_PLUGIN_ISOLATED,
        ),
        (
            {_ORDERED_PLUGIN_COMES_BEFORE_TARGET},
            _ORDERED_PLUGIN_HAS_COMES_BEFORE,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_AFTER},
            _ORDERED_PLUGIN_COMES_AFTER_TARGET,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL},
            _ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL,
        ),
    ],
)
async def test_get_comes_before(
    expected: set[_OrderedPluginDefinition], origin: _OrderedPluginDefinition
) -> None:
    assert (
        await get_comes_before(
            PluginManager(
                UNIVERSE,
                _OrderedPluginDefinition,
                [
                    _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
                    _ORDERED_PLUGIN_HAS_COMES_BEFORE,
                    _ORDERED_PLUGIN_COMES_AFTER_TARGET,
                    _ORDERED_PLUGIN_HAS_COMES_AFTER,
                    _ORDERED_PLUGIN_ISOLATED,
                    _ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL,
                    _ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL,
                ],
            ),
            origin,
        )
        == expected
    )
