"""
Provide configuration for the :py:class:`betty.extension.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any, Self

from typing_extensions import override

from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.serde.dump import minimize, Dump, VoidableDump
from betty.assertion import (
    RequiredField,
    OptionalField,
    assert_record,
    assert_path,
    assert_setattr,
)


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.
    """

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FamilyTreeConfiguration):
            return False
        return self._file_path == other.file_path

    @property
    def file_path(self) -> Path | None:
        """
        The path to the Gramps family tree file.
        """
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: Path | None) -> None:
        self._file_path = file_path

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("file", assert_path() | assert_setattr(self, "file_path"))
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return {"file": str(self.file_path) if self.file_path else None}

    @override
    def update(self, other: Self) -> None:
        self.file_path = other.file_path


class FamilyTreeConfigurationSequence(ConfigurationSequence[FamilyTreeConfiguration]):
    """
    Configure zero or more Gramps family trees.
    """

    @override
    def load_item(self, dump: Dump) -> FamilyTreeConfiguration:
        # Use a dummy path to satisfy initializer arguments.
        # It will be overridden when loading the fump.
        item = FamilyTreeConfiguration(Path())
        item.load(dump)
        return item


class GrampsConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.extension.gramps.Gramps` extension.
    """

    def __init__(
        self,
        *,
        family_trees: Iterable[FamilyTreeConfiguration] | None = None,
    ):
        super().__init__()
        self._family_trees = FamilyTreeConfigurationSequence(family_trees)

    @property
    def family_trees(self) -> FamilyTreeConfigurationSequence:
        """
        The Gramps family trees to load.
        """
        return self._family_trees

    @override
    def update(self, other: Self) -> None:
        self._family_trees.update(other._family_trees)

    @override
    def load(self, dump: Dump) -> None:
        assert_record(OptionalField("family_trees", self.family_trees.load))(dump)

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            {
                "family_trees": self.family_trees.dump(),
            },
            True,
        )
