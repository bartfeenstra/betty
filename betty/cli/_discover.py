from collections.abc import Mapping, Sequence
from importlib.metadata import EntryPoint, entry_points

from click import Command

from betty.importlib import import_any


def discover_commands() -> Mapping[str, Command]:
    betty_entry_points: Sequence[EntryPoint]
    betty_entry_points = entry_points(  # type: ignore[assignment, unused-ignore]
        group="betty.command",  # type: ignore[call-arg, unused-ignore]
    )
    return {
        betty_entry_point.name: import_any(betty_entry_point.value)
        for betty_entry_point in betty_entry_points
    }
