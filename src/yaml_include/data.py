import sys
from dataclasses import dataclass, field
from typing import Any

if sys.version_info >= (3, 9):
    from collections.abc import Mapping, Sequence
else:
    from typing import Mapping, Sequence

__all__ = ["Data"]


@dataclass(frozen=True)
class Data:
    """A :func:`dataclasses.dataclass` store YAML include statement"""

    urlpath: str
    """url/path of the YAML include statement

    urlpath can be either absolute (like `/usr/src/Python-1.5/*.yml`) or relative (like `../../Tools/*/*.yml`), and can contain shell-style wildcards.

    We support ``"**"``, ``"?"`` and ``"[..]"``. We do not support ``"^"`` for pattern negation.
    The ``maxdepth`` option is applied on the first ``"**"`` found in the path.

    Warning:
        Using the ``"**"`` pattern in large directory trees or remote files may consume an inordinate amount of time.
    """

    sequence_params: Sequence[Any] = field(default_factory=list)
    """sequence parameters of the YAML include statement.
    """

    mapping_params: Mapping[str, Any] = field(default_factory=dict)
    """mapping parameters of the YAML include statement
    """
