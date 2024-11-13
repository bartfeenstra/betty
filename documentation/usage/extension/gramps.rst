The *Gramps* extension
====================
The ``gramps`` extension loads entities from `Gramps <https://gramps-project.org>`_ family trees into your Betty ancestry.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            gramps: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "gramps": {}
            }
          }

Configuration
-------------
This extension is configurable:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            gramps:
              configuration:
                family_trees:
                  - file: ./gramps.gpkg
                    event-types:
                      GrampsEventType: betty-event-type
                      AnotherGrampsEventType: another-betty-event-type
                    genders:
                      F: female
                      M: male
                      U: unknown
                      NonBinary: non-binary
                    place-types:
                      GrampsPlaceType: betty-place-type
                      AnotherGrampsPlaceType: another-betty-place-type
                    presence-roles:
                      GrampsRole: betty-presence-role
                      AnotherGrampsRole: another-betty-presence-role

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "gramps": {
                "configuration" : {
                  "family_trees": [
                    {
                      "file": "./gramps.gpkg"
                      "event-types": {
                        "GrampsEventType: "betty-event-type",
                        "AnotherGrampsEventType: "another-betty-event-type"
                      },
                      "genders": {
                        "F: "female",
                        "M: "male",
                        "U: "unknown",
                        "NonBinary: "non-binary"
                      },
                      "place-types": {
                        "GrampsPlaceType: "betty-place-type",
                        "AnotherGrampsPlaceType: "another-betty-place-type"
                      },
                      "presence-roles": {
                        "GrampsRole: "betty-presence-role",
                        "AnotherGrampsRole: "another-betty-presence-role"
                      }
                    }
                  ]
                }
              }
            }
          }


All configuration options
^^^^^^^^^^^^^^^^^^^^^^^^^
- ``family_trees`` (required): An array defining zero or more Gramps family trees to load. Each item is an object with
  the following keys:

  - ``file`` (required): the path to a *Gramps XML* or *Gramps XML Package* file.
  - ``event_types`` (optional): how to map Gramps event types to Betty event types. Each keys is a Gramps event type,
    and each value is the plugin ID of the Betty event type to import the Gramps event type as.
  - ``genders`` (optional): how to map Gramps genders to Betty genders. Each keys is a Gramps gender,
    and each value is the plugin ID of the Betty gender to import the Gramps gender as.
  - ``place_types`` (optional): how to map Gramps place types to Betty place types. Each keys is a Gramps place type,
    and each value is the plugin ID of the Betty place type to import the Gramps place type as.
  - ``presence_roles`` (optional): how to map Gramps roles to Betty presence roles. Each keys is a Gramps role,
    and each value is the plugin ID of the Betty presence role to import the Gramps role as.

  If multiple family trees contain entities of the same type and with the same ID (e.g. a person with ID ``I1234``) each
  entity will overwrite any previously loaded entity.

Attributes
----------
Gramps allows arbitrary attributes to be added to some of its data types. Betty can parse these to load additional
information. Each of Betty's Gramps attributes follows the same structure: ``betty:...`` (to load the attribute for any
Betty project) or ``betty-MyProject:..`` (to load an attribute for the Betty project with machine name ``MyProject``),
where ``...`` is the name that identifies the attribute's meaning. For the 'privacy` attribute, the Gramps attribute's full
name would be ``betty:privacy`` or ``betty-MyProject:privacy``.

Privacy
^^^^^^^

Gramps has limited built-in support for people's privacy. To fully control privacy for people, as well as events, files,
sources, and citations, add a ``betty:privacy`` attribute to any of these types, with a value of ``private`` to explicitly
declare the data always private or ``public`` to declare the data always public. Any other value will leave the privacy
undecided, as well as person records marked public using Gramps' built-in privacy selector. In such cases, the
``privatizer`` extension may decide if the data is public or private.

Gender
^^^^^^
To set a person's gender to a gender that is available in Betty, but not in Gramps, add a ``betty:gender`` attribute,
whose value is the ID of the :doc:`/usage/ancestry/gender` you want to use.

Links
^^^^^

Gramps has limited built-in support to add links to entities. For those Gramps entities that support attributes,
you may add links using those:

.. list-table:: Link attributes
   :header-rows: 1

   * - Name
     - Required/optional
     - Description
   * - ``betty:link-LINKNAME:url``
     - **required**
     - The URL the link targets.
   * - ``betty:link-LINKNAME:description``
     - optional
     - A human-friendly longer link description.
   * - ``betty:link-LINKNAME:label``
     - optional
     - A human-friendly short link label.
   * - ``betty:link-LINKNAME:locale``
     - optional
     - An `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_.
   * - ``betty:link-LINKNAME:media_type``
     - optional
     - An `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
   * - ``betty:link-LINKNAME:relationship``
     - optional
     - An `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.

Where ``LINKNAME`` may be any value of your choosing, but must be unique per link. For example, where ``LINKNAME`` is ``cheese``:

.. list-table::

   * - ``betty:link-cheese:url``
     - ``https://en.wikipedia.org/wiki/Cheese``
   * - ``betty:link-cheese:label``
     - ``Learn about cheese``
   * - ``betty:link-cheese:description``
     - ``Read the Wikipedia article about cheese``

Dates
-----

For unknown date parts, set those to all zeroes and Betty will ignore them. For instance, ``0000-12-31`` will be parsed as
"December 31", and ``1970-01-00`` as "January, 1970".

Event types
-----------

Betty supports the following Gramps event types without any additional configuration:

.. list-table:: Event types
   :align: left
   :header-rows: 1

   * - Gramps event type
     - Betty event type
   * - ``Adopted``
     - ``adoption``
   * - ``Adult Christening``
     - ``baptism``
   * - ``Baptism``
     - ``baptism``
   * - ``Bar Mitzvah``
     - ``bar-mitzvah``
   * - ``Bat Mitzvah``
     - ``bat-mitzvah``
   * - ``Birth``
     - ``birth``
   * - ``Burial``
     - ``burial``
   * - ``Christening``
     - ``baptism``
   * - ``Confirmation``
     - ``confirmation``
   * - ``Cremation``
     - ``cremation``
   * - ``Death``
     - ``death``
   * - ``Divorce``
     - ``divorce``
   * - ``Divorce Filing``
     - ``divorce-announcement``
   * - ``Emigration``
     - ``emigration``
   * - ``Engagement``
     - ``engagement``
   * - ``Immigration``
     - ``immigration``
   * - ``Marriage``
     - ``marriage``
   * - ``Marriage Banns``
     - ``marriage-announcement``
   * - ``Occupation``
     - ``occupation``
   * - ``Residence``
     - ``residence``
   * - ``Retirement``
     - ``retirement``
   * - ``Will``
     - ``will``

Genders
-------

Betty supports the following Gramps genders without any additional configuration:

.. list-table:: Genders
   :align: left
   :header-rows: 1

   * - Gramps gender
     - Betty gender
   * - ``F``
     - ``female``
   * - ``M``
     - ``male``
   * - ``U``
     - ``unknown``

Place types
-----------

Betty supports the following Gramps place types without any additional configuration:

.. list-table:: Place types
   :align: left
   :header-rows: 1

   * - Gramps place type
     - Betty place type
   * - ``Borough``
     - ``borough``
   * - ``Building``
     - ``building``
   * - ``City``
     - ``city``
   * - ``Country``
     - ``country``
   * - ``County``
     - ``county``
   * - ``Department``
     - ``department``
   * - ``District``
     - ``district``
   * - ``Farm``
     - ``farm``
   * - ``Hamlet``
     - ``hamlet``
   * - ``Locality``
     - ``locality``
   * - ``Municipality``
     - ``municipality``
   * - ``Neighborhood``
     - ``neighborhood``
   * - ``Number``
     - ``number``
   * - ``Parish``
     - ``parish``
   * - ``Province``
     - ``province``
   * - ``Region``
     - ``region``
   * - ``State``
     - ``state``
   * - ``Street``
     - ``street``
   * - ``Town``
     - ``town``
   * - ``Unknown``
     - ``Unknown``
   * - ``Village``
     - ``village``

Presence roles
--------------

Betty supports the following Gramps presence roles without any additional configuration:

.. list-table:: Presence roles
   :align: left
   :header-rows: 1

   * - Gramps role
     - Betty presence role
   * - ``Aide``
     - ``attendee``
   * - ``Bride``
     - ``subject``
   * - ``Celebrant``
     - ``celebrant``
   * - ``Clergy``
     - ``celebrant``
   * - ``Family``
     - ``subject``
   * - ``Groom``
     - ``subject``
   * - ``Informant``
     - ``informant``
   * - ``Primary``
     - ``subject``
   * - ``Unknown``
     - ``unknown``
   * - ``Witness``
     - ``witness``

Order & priority
----------------

The order of lists of data, or the priority of individual bits of data, can be automatically determined by Betty in
multiple different ways, such as by matching dates, or locales. When not enough details are available, or in case of
ambiguity, the original order is preserved. If only a single item must be retrieved from the list, this will be the
first item, optionally after sorting.

For example, if a place has multiple names (which may be historical or translations), Betty may try to
filter names by the given locale and date, and then indiscriminately pick the first one of the remaining names to
display as the canonical name.

Tips:

- If you want one item to have priority over another, it should come before the other in a list (e.g. be higher up).
- Items with more specific or complete data, such as locales or dates, should come before items with less specific or
  complete data. However, items without dates at all are considered current and not historical.
- Unofficial names or nicknames, should generally be put at the end of lists.
