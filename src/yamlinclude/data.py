from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

__all__ = ["YamlIncludeData"]


@dataclass(frozen=True)
class YamlIncludeData:
    """A ``dataclass`` store YAML including statement"""

    urlpath: str
    """url/path of the YAML including statement

    urlpath can be either absolute (like `/usr/src/Python-1.5/*.yml`) or relative (like `../../Tools/*/*.yml`), and can contain shell-style wildcards.

    We support ``"**"``, ``"?"`` and ``"[..]"``. We do not support ``"^"`` for pattern negation.
    The ``maxdepth`` option is applied on the first ``"**"`` found in the path.

    Warning:
        Using the ``"**"`` pattern in large directory trees or remote files may consume an inordinate amount of time.
    """

    sequence_param: Sequence[Any] = field(default_factory=list)
    """sequence parameters of the YAML including statement.

    default: an empty list
    """

    mapping_param: Mapping[str, Any] = field(default_factory=dict)
    """mapping parameters of the YAML including statement

    default: an empty dictionary
    """
