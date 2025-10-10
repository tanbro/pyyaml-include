# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys

# -- Project information -----------------------------------------------------
if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyyaml-include"
copyright = "2023-2025, liu xue yan"
author = "liu xue yan"
# full version
version = importlib_metadata.version(project)
# major/minor version
release = ".".join(version.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx_tippy",
    "sphinx_inline_tabs",
    "sphinx_copybutton",
    "versionwarning.extension",
    "sphinx_autodoc_typehints",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for autodoc ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
# autodoc_mock_imports = []

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "both"

# Don't show class signature with the class' name.
# autodoc_class_signature = "separated"

autoclass_content = "both"
# autodoc_member_order = "bysource"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_theme_options = {
    "path_to_docs": "docs/",
    "repository_url": "https://github.com/tanbro/pyyaml-include",
    "repository_branch": "main",
    "use_download_button": True,
    "use_fullscreen_button": True,
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "show_toc_level": 2,
}


# -- Options for myst_parser extension ---------------------------------------

myst_enable_extensions = [
    "amsmath",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# -- Options for intersphinx extension ---------------------------------------

# configuration for intersphinx: refer to the Python standard and/or 3rd libraries.
intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
    "fsspec": ("https://filesystem-spec.readthedocs.io/en/latest/", None),
}

# -- Options for Napoleon settings ---------------------------------------
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
