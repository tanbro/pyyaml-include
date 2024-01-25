# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------

try:
    import importlib.metadata as importlib_metadata  # type: ignore
except ImportError:
    import importlib_metadata  # type: ignore

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyyaml-include"
copyright = "2023, liu xue yan"
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
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx_tippy",
    "sphinx_inline_tabs",
    "sphinx_copybutton",
    "versionwarning.extension",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for autodoc ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "description"

# Don't show class signature with the class' name.
# autodoc_class_signature = "separated"

autoclass_content = "both"
autodoc_member_order = "bysource"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/tanbro/pyyamlinclude",
    "source_branch": "master",
    "source_directory": "docs/",
    "top_of_page_button": "edit",
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
    "fsspec": ("https://filesystem-spec.readthedocs.io/en/stable/", None),
}

# -- Options for Napoleon settings ---------------------------------------
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
