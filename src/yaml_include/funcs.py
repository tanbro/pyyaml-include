import sys
from typing import Any, Generator, Mapping, MutableMapping, MutableSequence, Sequence

if sys.version_info < (3, 12):
    from .yaml_types_backward import TYamlLoaderTypes
else:
    from .yaml_types import TYamlLoaderTypes

from .constructor import Constructor
from .data import Data


__all__ = ["load", "lazy_load"]


def load(
    obj: Any,
    loader_type: TYamlLoaderTypes,
    constructor: Constructor,
    inplace: bool = False,
    nested: bool = False,
) -> Any:
    """Recursively load and parse all :class:`.Data` instances inside ``obj``.

    If :attr:`.Constructor.autoload` is ``False``, :func:`yaml.load` will not cause including files to be opened or read,
    in the situation, what returned by :func:`yaml.load` is an object with :class:`.Data` in it, and the files won't be processed.
    Thus we use the function to open and parse those including files represented by :class:`.Data` instances inside `obj`.

    Args:
        obj: object containers :class:`.Data`
        loader_type: use this type of `PyYAML` Loader to parse string in including file(s)
        constructor: use this :class:`.Constructor` to find/open/read including file(s)
        inplace: whether if make a in-place replacement for :class:`.Constructor` tags of including file(s) into ``obj`` argument
        nested: whether if parse and load include statement(s) inside including file(s)

    Return:
        Parsed object
    """
    if isinstance(obj, Data):
        d = constructor.load(loader_type, obj)
        if nested:
            return load(d, loader_type, constructor, inplace, nested)
        else:
            return d
    elif isinstance(obj, Mapping):
        if inplace:
            if not isinstance(obj, MutableMapping):
                raise ValueError(f"{obj} is not mutable")
            for k, v in obj.items():
                obj[k] = load(v, loader_type, constructor, inplace, nested)
        else:
            return {k: load(v, loader_type, constructor, inplace, nested) for k, v in obj.items()}
    elif isinstance(obj, Sequence) and not isinstance(obj, (bytearray, bytes, memoryview, str)):
        if inplace:
            if not isinstance(obj, MutableSequence):
                raise ValueError(f"{obj} is not mutable")
            for i, v in enumerate(obj):
                obj[i] = load(v, loader_type, constructor, inplace, nested)
        else:
            return [load(m, loader_type, constructor, inplace, nested) for m in obj]
    return obj


def lazy_load(
    obj: Any,
    loader_type: TYamlLoaderTypes,
    constructor: Constructor,
    nested: bool = False,
) -> Generator:
    """Recursively load and parse all :class:`.Data` inside ``obj`` in generative mode.

    Almost the same as :func:`.load`, except that:

    * The function returns a generator, it yield at every :class:`.Data` object found.
    * It only applies an in-place parsing and replacement, and will not return parsed object.
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
