Environment variables
=====================

Betty reads the following environment variables:

- ``BETTY_CACHE_DIRECTORY``: The path to a directory for Betty to use as its application cache. Defaults to ``.betty`` in the current user's home directory.
- ``BETTY_CONCURRENCY``: The concurrency factor expressed as an integer. Defaults to the number of CPU cores. Set to ``1``
  to disable concurrency altogether. Example: ``BETTY_CONCURRENCY=4``.
