Copyright notice plugins
========================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.copyright_notice.CopyrightNotice`
   * -  Repository
     -  :py:attr:`betty.project.Project.copyright_notice_repository`


Creating a copyright
--------------------

#. Create a new class that extends :py:class:`betty.copyright_notice.CopyrightNotice` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.copyright import CopyrightNotice
     from betty.machine_name import MachineName

     class MyCopyrightNotice(CopyrightNotice):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-copyright-notice"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your copyright notice by registering it as an entry point. Given the copyright notice above in a
module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.copyright_notice']
          'my-module-my-copyright-notice' = 'my_package.my_module.MyCopyrightNotice'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.copyright_notice': [
                      'my-module-my-copyright-notice=my_package.my_module.MyCopyrightNotice',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

See also
--------
Read more about how to use copyright notices and Betty's built-in copyright notices at :doc:`/usage/copyright-notice`.
