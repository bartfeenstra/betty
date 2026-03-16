GEDCOM
======

To build a site from your GEDCOM files, you must first convert them to *Gramps XML*:

#. Install and launch `Gramps <https://gramps-project.org/>`_
#. Create a new family tree
#. Import your GEDCOM file under *Family Trees* > *Import...*
#. Export your family tree under *Family Trees* > *Export...*
#. As output format, choose one of the *Gramps XML* options
#. Use the :py:class:`Gramps <betty.plugins.extension.gramps.Gramps>` extension to load the exported file
