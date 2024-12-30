from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

__all__ = ["Data"]


@dataclass(frozen=True)
class Data:
    """A :func:`dataclasses.dataclass` to store a YAML include statement."""

    urlpath: str
    """URL/path of the YAML include statement

    ``urlpath`` can be either absolute (e.g., `/usr/src/Python-1.5/*.yml`) or relative (e.g., `../../Tools/*/*.yml`) and can contain shell-style wildcards.

    We support ``"**"``, ``"?"``, and ``"[..]"``. We do not support ``"^"`` for pattern negation.
    The ``maxdepth`` option is applied to the first ``"**"`` found in the path.

    Warning:
        Using the ``"**"`` pattern in large directory trees or with remote files may consume a significant amount of time.
    """

    flatten: bool = False
    """Whether to flatten sequence objects parsed from multiple matched YAML files.

    * Only available when multiple files are matched.
    * **Each matched file must have a Sequence object at the top level**, otherwise a :class:`TypeError` exception will be raised.

    Example:
        Consider the following YAML:

        .. code-block:: yaml

            items: !include "*.yaml"

        If each file matching `*.yaml` contains a sequence object at the top level, the parsed and loaded result will be:

        .. code-block:: yaml

            items: [
                [item 0 of 1st file, item 1 of 1st file, ..., item n of 1st file],
                [item 0 of 2nd file, item 1 of 2nd file, ..., item n of 2nd file],
                # ...
                [item 0 of nth file, item 1 of nth file, ..., item n of nth file],
            ]

        This results in a 2-dimensional array because the YAML content of each matched file is treated as a member of the list (sequence).

        However, if the ``flatten`` parameter is set to ``true``, like:

        .. code-block:: yaml

            items: !include {urlpath: "*.yaml", flatten: true}

        the result will be:

        .. code-block:: yaml

            items: [
                item 0 of 1st file, item 1 of 1st file, ..., item n of 1st file,
                item 0 of 2nd file, item 1 of 2nd file, ..., item n of 2nd file,
                # ...
                item 0 of nth file, item 1 of nth file, ..., item n of nth file,
            ]
    """

    sequence_params: Sequence[Any] = field(default_factory=list)
    """sequence parameters of the YAML include statement.
    """

    mapping_params: Mapping[str, Any] = field(default_factory=dict)
    """mapping parameters of the YAML include statement
    """
