from betty.job.scheduler import (
    CyclicDependencyError,
    DuplicateJobError,
    UnknownJobError,
)


class TestCyclicDependencyError:
    def test_new(self) -> None:
        sut = CyclicDependencyError(["my-first-job", "my-second-job", "my-first-job"])
        assert (
            str(sut)
            == 'Job "my-first-job" has cyclic dependencies: "my-first-job" -> "my-second-job" -> "my-first-job".'
        )


class TestDuplicateJobError:
    def test_new(self) -> None:
        sut = DuplicateJobError("my-first-job")
        assert (
            str(sut)
            == 'Job "my-first-job" was added already, and cannot be added again.'
        )


class TestUnknownJobError:
    def test_new(self) -> None:
        sut = UnknownJobError("my-first-job")
        assert str(sut) == 'Job "my-first-job" was never added.'
