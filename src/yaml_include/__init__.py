"""
Include other YAML files in YAML
"""

__all__ = ["__version__", "version", "version_tuple", "Constructor", "Data", "lazy_load", "load", "Representer"]

from ._version import __version__, version, version_tuple
from .constructor import Constructor
from .data import Data
from .funcs import lazy_load, load
from .representer import Representer
