HTTP rate limit plugins
=======================

Rate limits ensure that Betty's :py:attr:`HTTP client <betty.app.App.http_client>` does not make more requests to an
address than that address supports or allows, by enforcing a maximum number of requests per timeframe.

Creating a rate limit
---------------------

Create a new class decorated with :py:class:`betty.http_client.rate_limit.RateLimitPlugin`, and that implements the
abstract methods, for example:

.. code-block:: python

   from betty.http_client.rate_limit import RateLimit, RateLimitPlugin

   @RateLimitPlugin(id="my-rate-limit")
   class MyRateLimit(RateLimit):
       # Implement remaining abstract methods...
       ...

Tell Betty about your rate limit by registering it as an entry point. Given the rate limit above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.http_rate_limit']
   'my-rate limit' = 'my_package.my_module.MyRateLimit'
