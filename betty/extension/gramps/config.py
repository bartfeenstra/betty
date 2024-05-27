"""
Provide configuration for the :py:class:`betty.extension.Gramps` extension.
"""

from __future__ import annotations

from typing import Iterable, Any, Self, TYPE_CHECKING

from typing_extensions import override

from betty.config import Configuration, ConfigurationSequence
from betty.serde.dump import minimize, Dump, VoidableDump
from betty.serde.load import Asserter, Fields, RequiredField, Assertions, OptionalField

if TYPE_CHECKING:
    from pathlib import Path


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.
    """

    def __init__(
        self,
        *,
        file_path: Path | None = None,
    ):
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
    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(
            Fields(
                RequiredField(
                    "file",
                    Assertions(asserter.assert_path())
                    | asserter.assert_setattr(configuration, "file_path"),
                ),
            )
        )(dump)
        return configuration

    @override
    def dump(self) -> VoidableDump:
        return {"file": str(self.file_path) if self.file_path else None}

    @override
    def update(self, other: Self) -> None:
        self.file_path = other.file_path
        self._dispatch_change()


class FamilyTreeConfigurationSequence(ConfigurationSequence[FamilyTreeConfiguration]):
    """
    Configure zero or more Gramps family trees.
    """

    @override
    @classmethod
    def _item_type(cls) -> type[FamilyTreeConfiguration]:
        return FamilyTreeConfiguration


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
        self._family_trees.on_change(self)

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
    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(
            Fields(
                OptionalField(
                    "family_trees",
                    Assertions(
                        configuration._family_trees.assert_load(
                            configuration.family_trees
                        )
                    ),
                ),
            )
        )(dump)
        return configuration

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            {
                "family_trees": self.family_trees.dump(),
            },
            True,
        )
