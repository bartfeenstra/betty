Versions
========

Betty releases follow `semantic versioning <https://semver.org/>`_ (*SemVer*). That means that each version number
follows the ``major.minor.patch`` format, e.g. ``2.7.19``, where

- ``major`` indicates the API version, and is incremented when releasing API changes
- ``minor`` is incremented when new functionality is added that does not change existing APIs
- ``patch`` is incremented when bugs are fixed that do not change existing APIs

Any change to ``minor`` or ``patch`` is backwards-compatible with previous releases with the same ``major``, e.g. if you
built a project or package based on Betty ``1.0.0``, any ``1.y.z`` release will be compatible.
