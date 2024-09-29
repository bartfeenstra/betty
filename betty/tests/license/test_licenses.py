from typing import Sequence

from typing_extensions import override

from betty.license import License
from betty.license.licenses import AllRightsReserved, PublicDomain
from betty.test_utils.license import LicenseTestBase


class TestAllRightsReserved(LicenseTestBase):
    @override
    def get_sut_class(self) -> type[License]:
        return AllRightsReserved

    @override
    def get_sut_instances(self) -> Sequence[License]:
        return [
            AllRightsReserved(),
        ]


class TestPublicDomain(LicenseTestBase):
    @override
    def get_sut_class(self) -> type[License]:
        return PublicDomain

    @override
    def get_sut_instances(self) -> Sequence[License]:
        return [
            PublicDomain(),
        ]
