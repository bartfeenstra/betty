Filters
=======

Jinja2 `filters <https://jinja.palletsprojects.com/en/3.1.x/templates/#filters>`_ are like function calls,
and specifically designed to transform data.
In addition to Jinja2's built-in filters, Betty provides the following:

- :py:func:`camel_case_to_kebab_case <betty.string.camel_case_to_kebab_case>`
- :py:func:`camel_case_to_snake_case <betty.string.camel_case_to_snake_case>`
- :py:func:`file <betty.jinja2.filter.filter_file>`
- :py:func:`flatten <betty.jinja2.filter.filter_flatten>`
- :py:func:`format_datey <betty.jinja2.filter.filter_format_datey>`
- :py:func:`format_degrees <betty.jinja2.filter.filter_format_degrees>`
- :py:func:`hashid <betty.jinja2.filter.filter_hashid>`
- :py:func:`image_resize_cover <betty.jinja2.filter.filter_image_resize_cover>`
- :py:func:`html_lang <betty.jinja2.filter.filter_html_lang>`
- :py:func:`json <betty.jinja2.filter.filter_json>`
- :py:func:`locale_get_data <betty.locale.get_data>`
- :py:func:`localize <betty.jinja2.filter.filter_localize>`
- :py:func:`localized_url <betty.jinja2.filter.filter_localized_url>`
- :py:func:`map <betty.jinja2.filter.filter_map>`
- :py:func:`negotiate_has_dates <betty.jinja2.filter.filter_negotiate_has_dates>`
- :py:func:`negotiate_localizeds <betty.jinja2.filter.filter_negotiate_localizeds>`
- :py:func:`paragraphs <betty.jinja2.filter.filter_paragraphs>`
- :py:func:`select_has_dates <betty.jinja2.filter.filter_select_has_dates>`
- :py:func:`select_localizeds <betty.jinja2.filter.filter_select_localizeds>`
- :py:func:`static_url <betty.jinja2.filter.filter_static_url>`
- :py:func:`sort_localizeds <betty.jinja2.filter.filter_sort_localizeds>`
- :py:func:`unique <betty.jinja2.filter.filter_unique>`
- :py:func:`upper_camel_case_to_lower_camel_case <betty.string.upper_camel_case_to_lower_camel_case>`
