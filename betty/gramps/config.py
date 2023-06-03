from __future__ import annotations

from pathlib import Path
from typing import Optional, Iterable, Type

from reactives.instance.property import reactive_property

from betty.config import Configuration, DumpedConfiguration, VoidableDumpedConfiguration, ConfigurationSequence
from betty.config.dump import minimize
from betty.config.load import Assertions, Fields, RequiredField, \
    OptionalField, Asserter
from betty.locale import Localizer

try:
    from typing_extensions import Self
except ModuleNotFoundError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover


class FamilyTreeConfiguration(Configuration):
    def __init__(self, file_path: Path | None = None):
        super().__init__()
        self.file_path = file_path

    def __eq__(self, other):
        if not isinstance(other, FamilyTreeConfiguration):
            return False
        return self._file_path == other.file_path

    @property
    @reactive_property
    def file_path(self) -> Path | None:
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: Path | None) -> None:
        self._file_path = file_path

    @classmethod
    def load(
            cls,
            dumped_configuration: DumpedConfiguration,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter(localizer=localizer)
        asserter.assert_record(Fields(
            RequiredField(
                'file',
                Assertions(asserter.assert_path()) | asserter.assert_setattr(configuration, 'file_path'),
            ),
        ))(dumped_configuration)
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        return {
            'file': str(self.file_path),
        }


class FamilyTreeConfigurationSequence(ConfigurationSequence[FamilyTreeConfiguration]):
    def update(self, other: Self) -> None:
        self._clear_without_trigger()
        self.append(*other)

    @classmethod
    def _create_default_item(cls, configuration_key: int) -> FamilyTreeConfiguration:
        return FamilyTreeConfiguration()

    @classmethod
    def _item_type(cls) -> Type[FamilyTreeConfiguration]:
        return FamilyTreeConfiguration


class GrampsConfiguration(Configuration):
    def __init__(self, family_trees: Optional[Iterable[FamilyTreeConfiguration]] = None):
        super().__init__()
        self._family_trees = FamilyTreeConfigurationSequence(family_trees)
        self._family_trees.react(self)

    @property
    def family_trees(self) -> FamilyTreeConfigurationSequence:
        return self._family_trees

    def update(self, other: Self) -> None:
        self._family_trees.update(other._family_trees)

    @classmethod
    def load(
            cls,
            dumped_configuration: DumpedConfiguration,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter(localizer=localizer)
        asserter.assert_record(Fields(
            OptionalField(
                'family_trees',
                Assertions(configuration._family_trees.assert_load(configuration.family_trees)),
            ),
        ))(dumped_configuration)
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        return minimize({
            'family_trees': self.family_trees.dump(),
        }, True)
