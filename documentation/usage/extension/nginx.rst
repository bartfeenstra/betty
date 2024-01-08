The nginx extension
===================
The nginx extension creates an `nginx <https://nginx.org>`_ configuration file and a `Docker <https://www.docker.com/>`_ ``Dockerfile`` in the output
directory. If ``content_negotiation`` is enabled. You must make sure the nginx
`Lua module <https://github.com/openresty/lua-nginx-module#readme>`_ is enabled, and
`CONE <https://github.com/bartfeenstra/cone>`_'s
`cone.lua <https://raw.githubusercontent.com/bartfeenstra/cone/master/cone.lua>`_ can be found by putting it in
nginx's `lua_package_path <https://github.com/openresty/lua-nginx-module#lua_package_path>`_. This is done
automatically when using the ``Dockerfile``.

Enable this extension through Betty Desktop, or in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. code-block:: yaml

    extensions:
      betty.extension.Nginx: ~

Configuration
-------------
This extension is configurable. Enable it in your project's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.Nginx:
        www_directory_path: /var/www/betty
        https: true

All configuration options
^^^^^^^^^^^^^^^^^^^^^^^^^
- ``https`` (optional): A boolean to enforce HTTPS in the nginx configuration.
  Defaults to whether the project's base URL uses HTTPS.
- ``www_directory_path`` (optional): A string to override the WWW directory path in the nginx configuration.
  Defaults to the project's WWW directory path.

Docker
------
The extension generates ``./nginx/Dockerfile`` inside your site's output directory. This image includes all dependencies
needed to serve your Betty site over HTTP (port 80).

To run Betty using this Docker image, configure the extension as follows:

.. code-block:: yaml

    extensions:
      betty.extension.nginx.Nginx:
        www_directory_path: /var/www/betty/ # This is the web root inside the container.
        https: false # HTTPS is currently not supported in the Docker container.

Then generate your site, and when starting the container based on the generated image, mount ``./nginx/nginx.conf`` and
``./www`` from the output directory to ``/etc/nginx/conf.d/betty.conf`` and ``/var/www/betty`` respectively.

You can choose to mount the container's port 80 to a port on your host machine, or set up a load balancer to proxy
traffic to the container.

HTTPS/SSL
^^^^^^^^^
The Docker image does not currently support secure connections
(`read more <https://github.com/bartfeenstra/betty/issues/1056>`_). For HTTPS support, you will have to set up a separate
web server to terminate SSL, and forward all traffic to the container over HTTP.