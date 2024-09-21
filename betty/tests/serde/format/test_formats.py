from collections.abc import Sequence

import pytest
from typing_extensions import override

from betty.serde.format import Format, FormatError
from betty.serde.format.formats import Json, Yaml
from betty.test_utils.serde.format import FormatTestBase


class TestJson(FormatTestBase):
    @override
    def get_sut_class(self) -> type[Format]:
        return Json

    @override
    def get_format_sut_instances(self) -> Sequence[Format]:
        return [Json()]

    def test_load_with_invalid_dump(self) -> None:
        with pytest.raises(FormatError):
            Json().load("InvalidJson")


class TestYaml(FormatTestBase):
    @override
    def get_sut_class(self) -> type[Format]:
        return Yaml

    @override
    def get_format_sut_instances(self) -> Sequence[Format]:
        return [Yaml()]

    def test_load_with_invalid_dump(self) -> None:
        with pytest.raises(FormatError):
            Yaml().load(": :InvalidYaml: :")
