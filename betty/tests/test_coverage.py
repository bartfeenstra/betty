from __future__ import annotations

from collections import defaultdict

from betty.fs import ROOT_DIRECTORY_PATH
from betty.test_utils.coverage import (
    Module,
    MissingReason,
    InternalModule,
    Function,
    Class,
)


# This baseline MUST NOT be extended. It SHOULD decrease in size as more coverage is added to Betty over time.
_BASELINE = Module(
    "betty",
    missing=MissingReason.SHOULD_BE_COVERED,
    children={
        InternalModule("betty._patch"),
        Module(
            "betty.about",
            missing=MissingReason.SHOULD_BE_COVERED,
            children={
                Function(
                    "betty.about:is_development",
                    missing=MissingReason.SHOULD_BE_COVERED,
                ),
                Function(
                    "betty.about:is_stable", missing=MissingReason.SHOULD_BE_COVERED
                ),
                Function("betty.about:report", missing=MissingReason.SHOULD_BE_COVERED),
            },
        ),
        Module(
            "betty.assets",
            missing=MissingReason.SHOULD_BE_COVERED,
            children={
                Class(
                    "betty.assets:AssetRepository",
                    missing=MissingReason.SHOULD_BE_COVERED,
                ),
            },
        ),
        InternalModule("betty.test_utils"),
        InternalModule("betty.tests"),
    },
)


class TestCoverage:
    async def test(self) -> None:
        errors = defaultdict(list)
        for error_file_path, error_message in _BASELINE.validate():
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
