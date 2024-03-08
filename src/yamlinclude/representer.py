__all__ = ["YamlIncludeRepr"]


class YamlIncludeRepr:
    """Representer for :class:`Data`

    When dumping an object into YAML string, it deserializes :class:`.Data`.

    Add the representer to `PyYAML Dumper` as below::

        repr_ = YamlIncludeRepr("inc")  # No "!" here !!!
        yaml.add_representer(yaml.Node, repr_, Dumper)
    """  # noqa: E501

    def __init__(self, tag: str):
        """
        Args:
            tag: YAML tag name used in including expression.

            Attention:
                Custom YAML tags start with ``"!"``,
                but we **MUST NOT** put a ``"!"`` at the beginning of ``tag`` here -- :func:`yaml.add_representer`` will add the symbol itself.
        """
        self._tag = tag

    def __call__(self, dumper, data):
        if data.mapping_param:
            params = {"urlpath": data.urlpath}
            params.update({k: v for k, v in data.mapping_param.items()})
            return dumper.represent_mapping(f"!{self._tag}", params)
        if data.sequence_param:
            params = [data.urlpath]
            params.extend(data.sequence_param)
            return dumper.represent_sequence(f"!{self._tag}", params)
        return dumper.represent_scalar(f"!{self._tag}", data.urlpath)
