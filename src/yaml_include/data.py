from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

__all__ = ["Data"]


@dataclass(frozen=True)
class Data:
    """A :func:`dataclasses.dataclass` store YAML include statement"""

    urlpath: str
    """url/path of the YAML include statement

    ``urlpath`` can be either absolute (like `/usr/src/Python-1.5/*.yml`) or relative (like `../../Tools/*/*.yml`), and can contain shell-style wildcards.

    We support ``"**"``, ``"?"`` and ``"[..]"``. We do not support ``"^"`` for pattern negation.
    The ``maxdepth`` option is applied on the first ``"**"`` found in the path.

    Warning:
        Using the ``"**"`` pattern in large directory trees or remote files may consume an inordinate amount of time.
    """

    flatten: bool = False
    """Whether to flatten sequence object pared from multiple matched YAML files.

    * Only available when multiple files were matched
    * **Every matched file should have a Sequence object in its top level**, or a :class:`TypeError` exception may be thrown.

    Example:
        Consider we have such a YAML:

        .. code-block:: yaml

            items: !include "*.yaml"

        If every file matches `*.yaml` contains a sequence object at the top level in it, what parsed and loaded will be:

        .. code-block:: yaml

                items: [
                    [item 0 of 1st file, item 1 of 1st file, ... , item n of 1st file, ...],
                    [item 0 of 2nd file, item 1 of 2nd file, ... , item n of 2nd file, ...],
                    # ....
                    [item 0 of nth file, item 1 of nth file, ... , item n of nth file, ...],
                    # ...
                ]

        It's a 2-dim array, because YAML content of each matched file is treated as a member of the list(sequence).

        But if ``flatten`` parameter was set to ``true``, like:

        .. code-block:: yaml

            items: !include {urlpath: "*.yaml", flatten: true}

        we'll get:

            .. code-block:: yaml

                items: [
                    item 0 of 1st file, item 1 of 1st file, ... , item n of 1st file,  # ...
                    item 0 of 2nd file, item 1 of 2nd file, ... , item n of 2nd file,  # ...
                    # ....
                    item 0 of n-th file, item 1 of n-th file, ... , item n of n-th file,  # ...
                    # ...
                ]
    """

    sequence_params: Sequence[Any] = field(default_factory=list)
    """sequence parameters of the YAML include statement.
    """

    mapping_params: Mapping[str, Any] = field(default_factory=dict)
    """mapping parameters of the YAML include statement
    """
