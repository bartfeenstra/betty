from typing import Callable, Dict

from voluptuous import Schema


class MapDict:
    def __init__(self, key_validator: Callable, value_validator: Callable):
        self._key_validator = Schema(key_validator)
        self._value_validator = Schema(value_validator)

    def __call__(self, v: Dict):
        return {self._key_validator(key): self._value_validator(value) for key, value in v.items()}
