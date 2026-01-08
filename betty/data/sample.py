"""
Data sample helpers.
"""

from __future__ import annotations

from typing import TypeVar, overload

from betty.config import Configuration
from betty.data import DataDefinition, HasData, Sample, SampleNotFound

_DataT = TypeVar("_DataT")
_HasDataT = TypeVar("_HasDataT", bound=HasData)
_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


@overload
def get_minimal_sample(data: type[_HasDataT], /) -> Sample[_HasDataT]:
    pass


@overload
def get_minimal_sample(data: DataDefinition[_DataT], /) -> Sample[_DataT]:
    pass


@overload
def get_minimal_sample(data: type[_ConfigurationT], /) -> Sample[_ConfigurationT]:
    pass


def get_minimal_sample(data):
    """
    Get a sample for a data type, preferably as minimal as possible.
    """
    if isinstance(data, type) and issubclass(data, HasData):
        data = data.data()
    samples = list(data.samples if isinstance(data, DataDefinition) else data.samples())
    for sample in samples:
        if sample.minimal:
            return sample
    for sample in samples:
        if not sample.full:
            return sample
    if samples:
        return samples[0]
    raise SampleNotFound


@overload
def get_full_sample(data: type[_HasDataT], /) -> Sample[_HasDataT]:
    pass


@overload
def get_full_sample(data: DataDefinition[_DataT], /) -> Sample[_DataT]:
    pass


@overload
def get_full_sample(data: type[_ConfigurationT], /) -> Sample[_ConfigurationT]:
    pass


def get_full_sample(data):
    """
    Get a sample for a data type, preferably as full as possible.
    """
    if isinstance(data, type) and issubclass(data, HasData):
        data = data.data()
    samples = list(data.samples if isinstance(data, DataDefinition) else data.samples())
    for sample in samples:
        if sample.full:
            return sample
    for sample in samples:
        if not sample.minimal:
            return sample
    if samples:
        return samples[0]
    raise SampleNotFound
