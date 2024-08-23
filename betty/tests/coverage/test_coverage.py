from __future__ import annotations

import pkgutil
from collections import defaultdict
from configparser import ConfigParser
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import TypeVar, Generic, Union, TYPE_CHECKING, Iterator, TypeAlias, override

from betty.fs import ROOT_DIRECTORY_PATH
from betty.importlib import import_any

if TYPE_CHECKING:
    from collections.abc import (
        Sequence,
    )


Errors: TypeAlias = Iterator[tuple[Path, str]]


class MissingReason(Enum):
    ABSTRACT = "This testable is abstract"
    COVERAGERC = "This testable is excluded by .coveragerc"
    INTERNAL = "This testable is internal to Betty itself"
    SHOULD_BE_COVERED = "This testable should be covered by a test but isn't yet"


@lru_cache
def get_coveragerc_ignore_modules() -> Sequence[Path]:
    coveragerc = ConfigParser()
    coveragerc.read(ROOT_DIRECTORY_PATH / ".coveragerc")
    omit = coveragerc.get("run", "omit").strip().split("\n")
    modules = []
    for omit_pattern in omit:
        for module_path in Path().glob(omit_pattern):
            if module_path.suffix != ".py":
                continue
            if not module_path.is_file():
                continue
            modules.append(module_path.resolve())
    return modules


def _name_to_path(fully_qualified_type_name: str) -> Path:
    module_name = (
        fully_qualified_type_name.rsplit(":", 1)[0]
        if ":" in fully_qualified_type_name
        else fully_qualified_type_name
    )
    return Path(import_any(module_name).__file__)


class _Testable:
    def __init__(self, name: str, *, missing: MissingReason | None = None):
        self._name = name
        self._missing = missing
        self._parent: _Testable | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def file_path(self) -> Path:
        return _name_to_path(self.name)

    @property
    def missing(self) -> MissingReason | None:
        return self._missing

    @property
    def parent(self) -> _Testable | None:
        return self._parent

    @parent.setter
    def parent(self, parent: _Testable) -> None:
        self._parent = parent

    def exists(self) -> bool:
        try:
            import_any(self.name)
            return True
        except ImportError:
            return False

    def validate(self) -> Errors:
        if self.missing and self.exists():
            yield self.file_path, "This was marked missing but unexpectedly exists"


_ChildT = TypeVar("_ChildT", bound=_Testable)


class HasChildren(_Testable, Generic[_ChildT]):
    def __init__(
        self,
        name: str,
        *,
        children: set[_ChildT],
        missing: MissingReason | None = None,
    ):
        super().__init__(name, missing=missing)
        self._children = children
        for child in self.children:
            child.parent = self

    @property
    def children(self) -> set[_ChildT]:
        return self._children

    @override
    def validate(self) -> Errors:
        yield from super().validate()
        for child in self.children:
            yield from child.validate()


class Function(_Testable):
    pass


class Method(_Testable):
    pass


class Class(HasChildren[Method]):
    pass


class Module(HasChildren[Union["Module", Class, Function]]):
    def __init__(
        self,
        name: str,
        *,
        children: set[Union["Module", Class, Function]],
        missing: MissingReason | None = None,
    ):
        super().__init__(name, children=children, missing=missing)
        child_module_names = {
            child.module_name for child in children if isinstance(child, Module)
        }
        for module_info in pkgutil.iter_modules(
            [str(Path(import_any(self.name).__file__))]
        ):
            if module_info.name not in child_module_names:
                self._children = {
                    *self._children,
                    Module(f"{self.name}.{module_info.name}", children=set()),
                }

    @property
    def module_name(self) -> str:
        return self.name.split(".")[-1]


class InternalModule(Module):
    def __init__(self, name: str):
        super().__init__(name, children=set(), missing=MissingReason.INTERNAL)


# This baseline MUST NOT be extended. It SHOULD decrease in size as more coverage is added to Betty over time.
TESTABLE = Module(
    "betty",
    missing=MissingReason.SHOULD_BE_COVERED,
    children={
        InternalModule("betty._patch"),
        Module(
            "betty.about",
            children={
                Function("is_development"),
                Function("is_stable"),
                Function("report"),
            },
        ),
        Module(
            "betty.assets",
            children={
                Class(
                    "betty.assets:AssetRepository",
                    children={
                        Method("betty.assets:AssetRepository.__len__"),
                        Method("betty.assets:AssetRepository.clear"),
                        Method("betty.assets:AssetRepository.paths"),
                        Method("betty.assets:AssetRepository.prepend"),
                    },
                ),
            },
        ),
    },
)


class TestCoverage:
    async def test(self) -> None:
        errors = defaultdict(list)
        for error_file_path, error_message in TESTABLE.validate():
            errors[error_file_path].append(error_message)
        if len(errors):
            message = "Missing test coverage:"
            total_error_count = 0
            for file_path in sorted(errors.keys()):
                file_error_count = len(errors[file_path])
                total_error_count += file_error_count
                if not file_error_count:
                    continue
                message += f"\n{file_path.relative_to(ROOT_DIRECTORY_PATH)}: {file_error_count} error(s)"
                for error in errors[file_path]:
                    message += f"\n  - {error}"
            message += f"\nTOTAL: {total_error_count} error(s)"

            raise AssertionError(message)
