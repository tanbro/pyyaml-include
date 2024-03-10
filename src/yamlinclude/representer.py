from dataclasses import dataclass

__all__ = ["YamlIncludeRepr"]


@dataclass
class YamlIncludeRepr:
    """Representer for :class:`yamlinclude.data.Data`

    When dumping an object into YAML string, it deserializes :class:`yamlinclude.data.Data`

    Add the representer to `PyYAML Dumper` as below::

        rpr = YamlIncludeRepr("inc")  # No "!" here !!!
        yaml.add_representer(YamlIncludeData, rpr)
    """

    tag: str
    """YAML tag name for include statement

    Attention:
        Custom YAML tag's name starts with ``"!"``.
        But we **MUST NOT** put a ``"!"`` at the beginning of here,
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
