"""
SPDX licenses.
"""

import re
import tarfile
from asyncio import gather, to_thread
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from io import BytesIO
from json import loads
from pathlib import Path
from typing import Final, Self, final, override

from aiohttp import ClientError, ClientSession

from betty.app import App
from betty.caches.file import BinaryFileCache
from betty.exception import HumanFacingException
from betty.factory import Manufacturable
from betty.file import read
from betty.license import License, LicenseDefinition
from betty.locale.localizable import Localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.plain import Plain
from betty.machine_name import MachineName
from betty.plugin.discovery import ResolvableDiscovery
from betty.portable import PortableData, PortableSequence
from betty.service_level import ServiceLevel
from betty.user import User

_spdx_license_id_pattern: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9-]")


def spdx_license_id_to_license_id(spdx_license_id: str, /) -> MachineName:
    """
    Get the Betty license plugin ID for the given SPDX license ID.
    """
    return MachineName(
        f"spdx-{_spdx_license_id_pattern.sub('--', spdx_license_id.lower())}"
    )


@final
class SpdxLicenseDiscoverer(Manufacturable):
    """
    Discover licenses from the `SPDX License List <https://spdx.org/licenses/>`_.
    """

    version: Final[str] = "3.27.0"
    url: Final[str] = (
        f"https://github.com/spdx/license-list-data/archive/refs/tags/v{version}.tar.gz"
    )

    def __init__(
        self,
        *,
        http_client: ClientSession,
        user: User,
        binary_file_cache: BinaryFileCache,
    ):
        self._http_client = http_client
        self._user = user
        self._cache_directory = (
            binary_file_cache
            .with_scope("spdx-licenses")
            .with_scope(self.version)
            .directory
        )

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(
            binary_file_cache=app.binary_file_cache.with_scope("spdx"),
            http_client=await app.http_client,
            user=app.user,
        )

    @classmethod
    async def discover_for(
        cls, services: ServiceLevel
    ) -> Iterable[ResolvableDiscovery[LicenseDefinition]]:
        """
        Discover SPDX licenses.
        """
        return await (await cls.new(services)).discover()

    async def discover(self) -> Iterable[ResolvableDiscovery[LicenseDefinition]]:
        """
        Discover the licenses.
        """
        if not self._cache_directory.exists():
            try:
                spdx_licenses_response = await self._http_client.get(self.url)
                spdx_licenses_data_tar = await spdx_licenses_response.read()
            except ClientError:
                await self._user.message_warning(
                    _("Betty could not load the SPDX licenses")
                )
                return [lambda _: ()]

            await to_thread(
                self._extract_licenses,
                spdx_licenses_data_tar,
                self._cache_directory,
            )

        spdx_licenses_data_json = await read(
            self._cache_directory
            / f"license-list-data-{self.version}"
            / "json"
            / "licenses.json"
        )
        spdx_data = loads(spdx_licenses_data_json)
        assert isinstance(spdx_data, Mapping)

        spdx_licenses_data = spdx_data["licenses"]
        assert isinstance(spdx_licenses_data, Sequence)

        return [lambda _: self._build_licenses_from_data(spdx_licenses_data)]

    async def _build_licenses_from_data(
        self, data: PortableSequence
    ) -> Iterable[LicenseDefinition]:
        return (
            license
            for license in await gather(  # noqa: A001
                *map(
                    self._build_license_from_data,
                    data,
                )
            )
            if license is not None
        )

    async def _build_license_from_data(
        self, data: PortableData
    ) -> LicenseDefinition | None:
        assert isinstance(data, Mapping)

        if data.get("isDeprecatedLicenseId", False):  # ty:ignore[no-matching-overload]
            return None

        spdx_license_id = data["licenseId"]  # ty:ignore[invalid-argument-type]
        assert isinstance(spdx_license_id, str)
        spdx_license_id_to_license_id(spdx_license_id)

        spdx_reference = data["reference"]  # ty:ignore[invalid-argument-type]
        assert isinstance(spdx_reference, str)

        return await self._build_license(spdx_license_id, spdx_reference)

    async def _build_license(self, license_id: str, url: str) -> LicenseDefinition:
        spdx_license_data_json = await read(
            self._cache_directory
            / f"license-list-data-{self.version}"
            / "json"
            / "details"
            / f"{license_id}.json"
        )

        with self._catch_json_errors():
            spdx_license_data = loads(spdx_license_data_json)
            assert isinstance(spdx_license_data, Mapping)

            license_name = spdx_license_data["name"]
            assert isinstance(license_name, str)

            license_text = spdx_license_data["licenseText"]
            assert isinstance(license_text, str)

            @LicenseDefinition(
                spdx_license_id_to_license_id(license_id), label=license_name
            )
            class _SpdxLicense(License):
                @override
                @property
                def summary(self) -> Localizable:
                    return self.plugin().label

                @override
                @property
                def text(self) -> Localizable:
                    return Plain(license_text)

                @override
                @property
                def url(self) -> Localizable | None:
                    return Plain(url)

            return _SpdxLicense.plugin()

    @classmethod
    def _extract_licenses(
        cls, spdx_licenses_data_tar: bytes, cache_directory: Path
    ) -> None:
        with tarfile.open(
            fileobj=BytesIO(spdx_licenses_data_tar), mode="r:gz"
        ) as tar_file:
            tar_file.extractall(
                cache_directory,
                members=[
                    tar_file.getmember(
                        f"license-list-data-{cls.version}/json/licenses.json"
                    ),
                    *[
                        tar_info
                        for tar_info in tar_file.getmembers()
                        if tar_info.name.startswith(
                            f"license-list-data-{cls.version}/json/details/"
                        )
                    ],
                ],
                filter="data",
            )

    @contextmanager
    def _catch_json_errors(self) -> Iterator[None]:
        try:
            yield
        except (AssertionError, LookupError) as error:
            raise HumanFacingException(
                Plain(f"Invalid JSON response received from {self.url}")
            ) from error
