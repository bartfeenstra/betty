Filters
=======

Jinja2 `filters <https://jinja.palletsprojects.com/en/3.1.x/templates/#filters>`_ are like function calls,
and specifically designed to transform data.
In addition to Jinja2's built-in filters, Betty provides the following:

- :py:func:`base64 <betty.jinja2.filter.filter_base64>`
- :py:func:`camel_case_to_kebab_case <betty.string.camel_case_to_kebab_case>`
- :py:func:`camel_case_to_snake_case <betty.string.camel_case_to_snake_case>`
- :py:func:`entity_type_name <betty.model.get_entity_type_name>`
- :py:func:`file <betty.jinja2.filter.filter_file>`
- :py:func:`flatten <betty.jinja2.filter.filter_flatten>`
- :py:func:`format_datey <betty.jinja2.filter.filter_format_datey>`
- :py:func:`format_degrees <betty.jinja2.filter.filter_format_degrees>`
- :py:func:`image <betty.jinja2.filter.filter_image>`
- :py:func:`json <betty.jinja2.filter.filter_json>`
- :py:func:`locale_get_data <betty.locale.get_data>`
- :py:func:`localize <betty.jinja2.filter.filter_localize>`
- :py:func:`map <betty.jinja2.filter.filter_map>`
- :py:func:`minimize <betty.serde.dump.minimize>`
- :py:func:`negotiate_dateds <betty.jinja2.filter.filter_negotiate_dateds>`
- :py:func:`negotiate_localizeds <betty.jinja2.filter.filter_negotiate_localizeds>`
- :py:func:`none_void <betty.serde.dump.none_void>`
- :py:func:`paragraphs <betty.jinja2.filter.filter_paragraphs>`
- :py:func:`select_dateds <betty.jinja2.filter.filter_select_dateds>`
- :py:func:`select_localizeds <betty.jinja2.filter.filter_select_localizeds>`
- :py:func:`static_url <betty.jinja2.filter.filter_static_url>`
- :py:func:`sort_localizeds <betty.jinja2.filter.filter_sort_localizeds>`
- :py:func:`tojson <betty.jinja2.filter.filter_tojson>`
- :py:func:`unique <betty.jinja2.filter.filter_unique>`
- :py:func:`upper_camel_case_to_lower_camel_case <betty.string.upper_camel_case_to_lower_camel_case>`
- :py:func:`url <betty.jinja2.filter.filter_url>`
- :py:func:`void_none <betty.serde.dump.void_none>`
- :py:func:`walk <betty.jinja2.filter.filter_walk>`
