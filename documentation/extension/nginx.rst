The nginx extension
===================

The *nginx* extension creates an `nginx <https://nginx.org>`_ configuration file and ``Dockerfile`` in the output
directory. If ``content_negotiation`` is enabled. You must make sure the nginx
`Lua module <https://github.com/openresty/lua-nginx-module#readme>`_ is enabled, and
`CONE <https://github.com/bartfeenstra/cone>`_'s
`cone.lua <https://raw.githubusercontent.com/bartfeenstra/cone/master/cone.lua>`_ can be found by putting it in
nginx's `lua_package_path <https://github.com/openresty/lua-nginx-module#lua_package_path>`_. This is done
automatically when using the ``Dockerfile``.

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
(`read more <https://github.com/bartfeenstra/betty/issues/511>`_). For HTTPS support, you will have to set up a separate
web server to terminate SSL, and forward all traffic to the container over HTTP.

Configuration
-------------
This extension is configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.nginx.Nginx:
        www_directory_path: /var/www/betty
        https: true

* ``www_directory_path`` (optional): The public www directory where Betty will be deployed. Defaults to ``www`` inside
  the output directory.
* ``https`` (optional): Whether or not nginx will be serving Betty over HTTPS. Most upstream nginx servers will
  want to have this disabled, so the downstream server can terminate SSL and communicate over HTTP 2 instead.
  Defaults to ``true`` if the base URL specifies HTTPS, or ``false`` otherwise.
