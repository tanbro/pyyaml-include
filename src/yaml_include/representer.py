from dataclasses import dataclass

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

    def __call__(self, dumper, data):  # type: ignore[no-untyped-def]
        if not isinstance(data, Data):  # pragma: no cover
            raise TypeError(f"Type of data for {type(self)} expects {Data}, but actually {type(data)}")

        if data.mapping_params:
            kv_args = {"urlpath": data.urlpath}
            kv_args.update(data.mapping_params)
            return dumper.represent_mapping(f"!{self.tag}", kv_args)
        if data.sequence_params:
            pos_args = [data.urlpath]
            pos_args.extend(data.sequence_params)
            return dumper.represent_sequence(f"!{self.tag}", pos_args)
        return dumper.represent_scalar(f"!{self.tag}", data.urlpath)
