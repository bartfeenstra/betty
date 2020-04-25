from os import path

from voluptuous import Invalid

from betty.importlib import import_any


def Path():
    def _path(v):
        try:
            return path.abspath(path.expanduser(v))
        except TypeError as e:
            raise Invalid(e)

    return _path


def Importable():
    def _importable(v):
        try:
            return import_any(v)
        except ImportError as e:
            raise Invalid(e)

    return _importable
