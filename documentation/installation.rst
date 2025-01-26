Installation
============

To use Betty, you must first :ref:`install Betty's requirements <installation-requirements>` and then
:ref:`install Betty itself <installation-betty>`.

.. _installation-requirements:

Installing requirements
-----------------------

Linux, macOS, or Windows
^^^^^^^^^^^^^^^^^^^^^^^^

You must use one of these desktop operating systems to be able to run Betty.

Python
^^^^^^

Betty requires `Python <https://www.python.org/>`_ 3.11 or higher.

.. _installation-requirements-nodejs:

Node.js
^^^^^^^

Some optional parts of Betty use third-party `JavaScript <https://en.wikipedia.org/wiki/JavaScript>`_
packages to help build your site.

If Betty shows you an error telling you you need *npm* or *Node.js*, then in order to use that functionality,
you must:

#. `install Node.js <https://nodejs.org/en/download/>`_ 20 or higher following the instructions shown there
#. ensure ``npm`` (the Node.js package manager) is in your ``PATH``, e.g. that ``npm`` can be run in a terminal
   from anywhere. When running ``npm --help`` in a terminal shows you npm's usage instructions, then you're all set.

Poppler
^^^^^^^

If your ancestry includes PDF files, then Betty requires `Poppler <https://poppler.freedesktop.org/>`_.
There several ways to install this, including but not limited to:

Linux: Debian, Ubuntu, etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run ``apt install poppler-utils``

Linux: CentOS, Fedora, RHEL, etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run ``yum install poppler-utils``

macOS
~~~~~

Install with `Homebrew <https://brew.sh/>`_: ``brew install poppler``

Windows
~~~~~~~

Install with `Scoop <https://scoop.sh/>`_: ``scoop install main/poppler``

.. _installation-betty:

Installing Betty itself
-----------------------

Use one of the following methods:

pip
^^^

Run ``pip install betty`` to install the latest stable release.

pipx
^^^^

Run ``pipx install betty`` to install the latest stable release.

poetry
^^^^^^

Run ``poetry add betty`` to install the latest stable release.

From source
^^^^^^^^^^^

This also requires *Bash*.

Run the following to install the latest unstable version:

#. ``git clone https://github.com/bartfeenstra/betty.git``
#. ``cd betty``
#. ``./bin/build``
