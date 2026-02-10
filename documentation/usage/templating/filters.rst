Filters
=======

Jinja2 `filters <https://jinja.palletsprojects.com/en/3.1.x/templates/#filters>`_ are like function calls,
and specifically designed to transform data.

Built-in filters
----------------
In addition to Jinja2's built-in filters, Betty provides the following:

- :py:func:`camel_case_to_kebab_case <betty.string.camel_case_to_kebab_case>`
- :py:func:`camel_case_to_snake_case <betty.string.camel_case_to_snake_case>`
- :py:func:`file <betty.jinja.filter.filter_file>`
- :py:func:`flatten <betty.jinja.filter.filter_flatten>`
- :py:func:`format_datetime_datetime <betty.jinja.filter.filter_format_datetime_datetime>`
- :py:func:`format_degrees <betty.jinja.filter.filter_format_degrees>`
- :py:func:`hashid <betty.hashid.hashid>`
- :py:func:`image_resize_cover <betty.jinja.filter.filter_image_resize_cover>`
- :py:func:`html_lang <betty.jinja.filter.filter_html_lang>`
- :py:func:`json_dump <betty.jinja.filter.filter_json_dump>`
- :py:func:`json_load <betty.jinja.filter.filter_json_load>`
- :py:func:`localize <betty.jinja.filter.filter_localize>`
- :py:func:`map <betty.jinja.filter.filter_map>`
- :py:func:`negotiate_has_dates <betty.jinja.filter.filter_negotiate_has_dates>`
- :py:func:`negotiate_has_locales <betty.jinja.filter.filter_negotiate_has_locales>`
- :py:func:`provide_content <betty.jinja.filter.filter_provide_content>`
- :py:func:`select_has_dates <betty.jinja.filter.filter_select_has_dates>`
- :py:func:`select_has_locales <betty.jinja.filter.filter_select_has_locales>`
- :py:func:`sort_has_locales <betty.jinja.filter.filter_sort_has_locales>`
- :py:class:`str <str>`
- :py:func:`to_language_tag <betty.locale.to_language_tag>`
- :py:func:`unique <betty.jinja.filter.filter_unique>`
- :py:func:`upper_camel_case_to_lower_camel_case <betty.string.upper_camel_case_to_lower_camel_case>`
- :py:func:`url <betty.jinja.filter.filter_url>`
