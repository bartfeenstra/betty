import pathlib

from voluptuous import Invalid

from betty.extension import Extension
from betty.importlib import import_any


def Path():
    def _path(v):
        try:
            return pathlib.Path(v).expanduser().resolve()
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


def ExtensionType():
    def _extension_type(extension_type_name):
        extension_type = Importable()(extension_type_name)
        try:
            if not issubclass(extension_type, Extension):
                raise Invalid('"%s" is not a Betty extension.' % extension_type_name)
        except TypeError:
            raise Invalid('"%s" is not a Betty extension.' % extension_type_name)
        return extension_type

    return _extension_type
