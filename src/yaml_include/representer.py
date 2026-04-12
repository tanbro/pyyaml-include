from dataclasses import dataclass
from itertools import chain

from yaml import Node
from yaml.representer import BaseRepresenter

from .data import Data

__all__ = ["Representer"]


@dataclass
class Representer:
    """Representer for :class:`.Data`

    When dumping an object into a YAML string, this representer serializes :class:`.Data` instances within the object.

    To add the representer to the ``PyYAML`` ``Dumper`` class, use the following code::

        import yaml_include

        rpr = yaml_include.Representer("inc")  # Note: No "!" prefix needed
        yaml.add_representer(Data, rpr)
    """

    tag: str
    """YAML tag name for include statement (without the "!" prefix)

    The "!" prefix is automatically added by :func:`yaml.add_representer`.

    Example:
        >>> rpr = yaml_include.Representer("inc")  # Creates "!inc" tag
    """

    def __call__(self, dumper: BaseRepresenter, data: Data) -> Node:
        if not isinstance(data, Data):  # pragma: no cover
            raise TypeError(f"{type(data)}")
        tag = "!" + self.tag
        if data.mapping_params:
            return dumper.represent_mapping(tag, {**{"urlpath": data.urlpath}, **data.mapping_params})
        if data.sequence_params:
            return dumper.represent_sequence(tag, chain((data.urlpath,), data.sequence_params))
        return dumper.represent_scalar(tag, data.urlpath)
