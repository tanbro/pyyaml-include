from dataclasses import dataclass

from .data import Data  # noqa: F401

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

    def __call__(self, dumper, data):
        if data.mapping_params:
            params = {"urlpath": data.urlpath}
            params.update({k: v for k, v in data.mapping_params.items()})
            return dumper.represent_mapping(f"!{self.tag}", params)
        if data.sequence_params:
            params = [data.urlpath]
            params.extend(data.sequence_params)
            return dumper.represent_sequence(f"!{self.tag}", params)
        return dumper.represent_scalar(f"!{self.tag}", data.urlpath)
