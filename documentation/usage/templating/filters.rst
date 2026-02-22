Filters
=======

Jinja2 `filters <https://jinja.palletsprojects.com/en/3.1.x/templates/#filters>`_ are like function calls,
and specifically designed to transform data.

Built-in filters
----------------
In addition to Jinja2's built-in filters, Betty provides the following:

- :py:func:`file <betty.jinja.filter.filter_file>`
- :py:func:`format_datetime_datetime <betty.jinja.filter.filter_format_datetime_datetime>`
- :py:func:`format_degrees <betty.jinja.filter.filter_format_degrees>`
- :py:func:`image_resize_cover <betty.jinja.filter.filter_image_resize_cover>`
- :py:func:`html_lang <betty.jinja.filter.filter_html_lang>`
- :py:func:`json_dump <betty.jinja.filter.filter_json_dump>`
- :py:func:`json_load <betty.jinja.filter.filter_json_load>`
- :py:func:`localize <betty.jinja.filter.filter_localize>`
- :py:func:`negotiate_has_dates <betty.jinja.filter.filter_negotiate_has_dates>`
- :py:func:`build_content <betty.jinja.filter.filter_build_content>`
- :py:func:`select_has_dates <betty.jinja.filter.filter_select_has_dates>`
- :py:func:`to_language_tag <betty.locale.to_language_tag>`
- :py:func:`unique <betty.jinja.filter.filter_unique>`
- :py:func:`url <betty.jinja.filter.filter_url>`
