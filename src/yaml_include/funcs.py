from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, Mapping, MutableMapping, MutableSequence, Sequence, Type, Union

from .constructor import Constructor
from .data import Data

if TYPE_CHECKING:  # pragma: no cover
    from yaml.cyaml import _CLoader
    from yaml.loader import _Loader


__all__ = ["load", "lazy_load"]


def load(
    obj: Any,
    loader_type: Type[Union[_Loader, _CLoader]],
    constructor: Constructor,
    inplace: bool = False,
    nested: bool = False,
) -> Any:
    """Recursively load and parse all :class:`.Data` instances inside ``obj``.

    If :attr:`.Constructor.autoload` is set to ``False``, :func:`yaml.load` will not open or read included files.
    In this case, :func:`yaml.load` returns an object containing :class:`.Data` instances, but the included files remain unprocessed.
    This function is used to open and parse those included files represented by :class:`.Data` instances within ``obj``.

    Args:
        obj: An object containing :class:`.Data` instances.
        loader_type: The type of PyYAML Loader to use for parsing strings in included files.
        constructor: The :class:`.Constructor` instance used to find, open, and read included files.
        inplace: Whether to perform in-place replacement for each :class:`.Data` instance in ``obj``.

        nested: Whether to recursively parse and load "include statements" inside :class:`.Data` instances.

            Note:
                The parameter is used for "include within include" scenarios, allowing nested includes.

    Returns:
        The fully parsed object with all included files loaded and processed.

    Warning:
        The function is **recursive** and can lead to a **stack overflow** if the ``obj`` is too deeply nested.
    """
    if isinstance(obj, Data):
        d = constructor.load(loader_type, obj)
        if nested:
            return load(d, loader_type, constructor, inplace, nested)
        else:
            return d
    elif isinstance(obj, Mapping):
        if inplace:
            if not isinstance(obj, MutableMapping):  # pragma: no cover
                raise ValueError(f"{obj} is not mutable")
            for k, v in obj.items():
                obj[k] = load(v, loader_type, constructor, inplace, nested)
        else:
            return {k: load(v, loader_type, constructor, inplace, nested) for k, v in obj.items()}
    elif isinstance(obj, Sequence) and not isinstance(obj, (bytearray, bytes, memoryview, str)):
        if inplace:
            if not isinstance(obj, MutableSequence):  # pragma: no cover
                raise ValueError(f"{obj} is not mutable")
            for i, v in enumerate(obj):
                obj[i] = load(v, loader_type, constructor, inplace, nested)
        else:
            return [load(m, loader_type, constructor, inplace, nested) for m in obj]
    return obj


def lazy_load(
    obj: Any, loader_type: Type[Union[_Loader, _CLoader]], constructor: Constructor, nested: bool = False
) -> Generator[Any, None, Any]:
    """Recursively load and parse all :class:`.Data` instances inside ``obj`` in generative mode.

    This function is similar to :func:`.load`, with the following differences:

    * It returns a :term:`generator` that yields each :class:`.Data` instance found within ``obj``.
    * It performs in-place parsing and replacement, but does not return the fully parsed object.

    Yields:
        Object parsed from the :class:`.Data` instances as one is encountered.
    """
    if isinstance(obj, Data):
        d = constructor.load(loader_type, obj)
        if nested:
            return (yield from lazy_load(d, loader_type, constructor, nested))
        else:
            return d
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = yield from lazy_load(v, loader_type, constructor, nested)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = yield from lazy_load(v, loader_type, constructor, nested)
    return obj
