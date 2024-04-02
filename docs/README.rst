README
######

.. include:: ../README.md
   :parser: myst_parser.sphinx_

How to build docs
=================

#. This documentation is made with `Sphinx <https://www.sphinx-doc.org/>`_, be sure to install it's dependencies:

   .. code:: sh

      pip install -r docs/requirements.txt

   Ignore this step if requirements already installed.

#. (*Optional*) Re-generate API-Docs, if source tree changed:

   .. code:: sh

      sphinx-apidoc -o docs/apidocs -eMTf src/yaml_include src/yaml_include/yaml_types*

#. Build HTML documentation:

   .. code:: sh

      docs/make html

The built static web site is output to ``docs/_build/html``, we can serve it:

.. code:: sh

   python -m http.server -d docs/_build/html

then open http://localhost:8000/ in a web browser.

.. tip::
   Try another port if ``8000`` is already in use.
   For example, to serve on port ``8080``:

   .. code:: sh

      python -m http.server -d docs/_build/html 8080

   .. seealso:: Python ``stdlib``'s :mod:`http.server`
