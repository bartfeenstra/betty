Tests
=====

Jinja2 `tests <https://jinja.palletsprojects.com/en/3.1.x/templates/#tests>`_ are like function calls,
and specifically designed to check a condition and return a boolean.

Built-in tests
--------------
In addition to Jinja2's built-in tests, Betty provides the following:

- :py:func:`asset_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`command_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`content_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`copyright_notice_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`entity_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`event_type_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`extension_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`gender_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`has_file_references <betty.jinja.test.test_has_file_references>`
- :py:func:`http_rate_limit_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`image_supported_media_type <betty.jinja.test.test_image_supported_media_type>`
- :py:func:`license_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`linked_data_dumpable <betty.jinja.test.test_linked_data_dumpable>`
- :py:func:`persistent_entity_id <betty.model.persistent_id>`
- :py:func:`place_type_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`role_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`public <betty.privacy.is_public>`
- :py:func:`renderer_plugin <betty.jinja.test.PluginTester.__call__>`
- :py:func:`serializer_plugin <betty.jinja.test.PluginTester.__call__>`
