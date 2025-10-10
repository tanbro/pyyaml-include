README
######

.. include:: ../README.md
   :parser: myst_parser.sphinx_

How to Build the Documentation
==============================

#. The documentation is built using `Sphinx`_.

   We need to install the package itself in editable mode, `Sphinx`_, and some of its extensions used in the documentation:

   * Using `pip`_:

     .. code:: sh

        pip install -e . --group docs

   * Using `uv`_:

     .. code:: sh

        uv sync --group docs

#. Generate API documentation.

   If it's the first time building the documentation, or if the source tree has changed, you may need a clean ``docs/apidoc`` directory and regenerate the API documentation:

   .. code:: sh

      sphinx-apidoc -H "" -feo docs/apidoc src

#. Build HTML documentation:

   * Using the Make tool (on Unix-like systems):

     .. code:: sh

        make -C docs html

   * On Windows:

     .. code:: bat

        docs\make html

The built static website is located at ``docs/_build/html``. You can serve it with a simple HTTP server:

.. code:: sh

   python -m http.server -d docs/_build/html

Then open http://localhost:8000/ in a web browser.

.. tip::
   Try another port if ``8000`` is already in use.
   For example, to serve on port ``8080``:

   .. code:: sh

      python -m http.server -d docs/_build/html 8080

   .. seealso:: Python ``stdlib``'s :mod:`http.server`


.. _sphinx: https://www.sphinx-doc.org/
.. _pip: https://pip.pypa.io/en/stable/
.. _uv: https://docs.astral.sh/uv/
