Installation from source
========================
These instructions are focused on setting up a Betty development environment.

Requirements
------------
- **Linux**, **macOS**, or **Windows**
- **Python 3.11+**
- `Node.js 16+ <https://nodejs.org/>`_ (required by some extensions)
- `ShellCheck <https://www.shellcheck.net/>`_
- `Xvfb <https://x.org/releases/X11R7.7/doc/man/man1/Xvfb.1.xhtml>`_
- The Cypress
  `system requirements <https://docs.cypress.io/guides/getting-started/installing-cypress#System-requirements>`_ and
  `individual packages <https://docs.cypress.io/guides/continuous-integration/introduction#Dependencies>`_ (headless Linux only)
- Bash

Instructions
------------
#. ``git clone https://github.com/bartfeenstra/betty.git``
#. ``cd betty``
#. ``./bin/build-dev``
