Tests
=====

Jinja2 `tests <https://jinja.palletsprojects.com/en/3.1.x/templates/#tests>`_ are like function calls,
and specifically designed to check a condition and return a boolean.
In addition to Jinja2's built-in tests, Betty provides the following:

- :py:func:`date_range <betty.jinja2.test.test_date_range>`
- :py:func:`end_of_life_event <betty.jinja2.test.test_end_of_life_event>`
- :py:func:`entity <betty.jinja2.test.TestEntity>`
- :py:func:`has_file_references <betty.jinja2.test.test_has_file_references>`
- :py:func:`persistent_entity_id <betty.model.persistent_id>`
- :py:func:`has_links <betty.jinja2.test.test_has_links>`
- :py:func:`linked_data_dumpable <betty.jinja2.test.test_linked_data_dumpable>`
- :py:func:`private <betty.privacy.is_private>`
- :py:func:`public <betty.privacy.is_public>`
- :py:func:`start_of_life_event <betty.jinja2.test.test_start_of_life_event>`
- :py:func:`subject_role <betty.jinja2.test.test_subject_role>`
- :py:func:`user_facing_entity <betty.jinja2.test.test_user_facing_entity>`
- :py:func:`witness_role <betty.jinja2.test.test_witness_role>`
