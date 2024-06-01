from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from yaml import Dumper, Node

from .data import Data

__all__ = ["Representer"]


@dataclass
class Representer:
    """Representer for :class:`.Data`

    When dumping an object into YAML string, it deserializes :class:`.Data` instance(s) in it.

    Add the representer to ``PyYAML`` ``Dumper`` class as below::

        import yaml_include

        rpr = yaml_include.Representer("inc")  # ATTENTION: No "!" here !!!
        yaml.add_representer(Data, rpr)
    """

    tag: str
    """YAML tag name for include statement

    Attention:
        Custom YAML tag's name starts with ``"!"``.
        But we **MUST NOT** put a ``"!"`` at the beginning here,
        because :func:`yaml.add_representer` will add the symbol itself.
    """

    def __call__(self, dumper: Dumper, data: Data) -> Node:
        if not isinstance(data, Data):  # pragma: no cover
            raise TypeError(f"{type(data)}")
        tag = "!" + self.tag
        if data.mapping_params:
            return dumper.represent_mapping(tag, {**{"urlpath": data.urlpath}, **data.mapping_params})
        if data.sequence_params:
            return dumper.represent_sequence(tag, chain((data.urlpath,), data.sequence_params))
        return dumper.represent_scalar(tag, data.urlpath)
