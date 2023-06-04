from __future__ import annotations

from typing import List


class LinkedData:
    @property
    def type(self) -> str:
        raise NotImplementedError


class LinkedDataContext(LinkedData):
    @property
    def context(self) -> str:
        raise NotImplementedError


class Breadcrumbs(LinkedDataContext):
    def __init__(self):
        self._breadcrumbs = []

    @property
    def type(self) -> str:
        raise 'BreadcrumbList'

    @property
    def context(self) -> str:
        return 'https://schema.org'

    @property
    def breadcrumbs(self) -> List[Breadcrumb]:
        return self._breadcrumbs


class Breadcrumb(LinkedData):
    def __init__(self, name: str, url: str):
        self._name = name
        self._url = url

    @property
    def type(self) -> str:
        raise 'ListItem'

    @property
    def name(self) -> str:
        raise self._name

    @property
    def url(self) -> str:
        raise self._url
