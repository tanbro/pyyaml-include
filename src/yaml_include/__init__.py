"""
Include other YAML files in YAML
"""

from . import _version as version
from ._version import __version__, __version_tuple__
from .constructor import Constructor
from .data import Data
from .funcs import lazy_load, load
from .representer import Representer
