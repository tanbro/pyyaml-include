import sys
from typing import Any, Generator, Mapping, MutableMapping, MutableSequence, Sequence

if sys.version_info < (3, 12):
    from .yamltypes_backward import TYamlLoaderTypes
else:
    from .yamltypes import TYamlLoaderTypes

from .constructor import YamlIncludeCtor
from .data import YamlIncludeData


__all__ = ["yamlinclude_load", "yamlinclude_lazy_load"]


def yamlinclude_load(
    obj: Any,
    loader_type: TYamlLoaderTypes,
    constructor: YamlIncludeCtor,
    inplace: bool = False,
    nested: bool = False,
) -> Any:
    """Recursively load and parse all :class:`.YamlIncludeData` instances inside ``obj``.

    If :attr:`.YamlIncludeCtor.autoload` is ``False``, :func:`yaml.load` will not cause including files to be opened or read,
    in the situation, what returned by :func:`yaml.load` is an object with :class:`.YamlIncludeData` in it, and the files won't be processed.
    Thus we use the function to open and parse those including files represented by :class:`.YamlIncludeData` instances inside `obj`.

    Args:
        obj: object containers :class:`.YamlIncludeData`
        loader_type: use this type of `PyYAML` Loader to parse string in including file(s)
        constructor: use this :class:`.YamlIncludeCtor` to find/open/read including file(s)
        inplace: whether if make a in-place replacement for :class:`.YamlIncludeCtor` tags of including file(s) into ``obj`` argument
        nested: whether if parse and load include statement(s) inside including file(s)

    Return:
        Parsed object
    """
    if isinstance(obj, YamlIncludeData):
        d = constructor.load(loader_type, obj)
        if nested:
            return yamlinclude_load(d, loader_type, constructor, inplace, nested)
        else:
            return d
    elif isinstance(obj, Mapping):
        if inplace:
            if not isinstance(obj, MutableMapping):
                raise ValueError(f"{obj} is not mutable")
            for k, v in obj.items():
                obj[k] = yamlinclude_load(v, loader_type, constructor, inplace, nested)
        else:
            return {
                k: yamlinclude_load(v, loader_type, constructor, inplace, nested)
                for k, v in obj.items()
            }
    elif isinstance(obj, Sequence) and not isinstance(
        obj, (bytearray, bytes, memoryview, str)
    ):
        if inplace:
            if not isinstance(obj, MutableSequence):
                raise ValueError(f"{obj} is not mutable")
            for i, v in enumerate(obj):
                obj[i] = yamlinclude_load(v, loader_type, constructor, inplace, nested)
        else:
            return [
                yamlinclude_load(m, loader_type, constructor, inplace, nested)
                for m in obj
            ]
    return obj


def yamlinclude_lazy_load(
    obj: Any,
    loader_type: TYamlLoaderTypes,
    constructor: YamlIncludeCtor,
    nested: bool = False,
) -> Generator:
    """Recursively load and parse all :class:`.YamlIncludeData` inside ``obj`` in generative mode.

    Almost the same as :func:`.yamlinclude_load`, except that:

    * The function returns a generator, it yield at every :class:`.YamlIncludeData` object found.
    * It only applies an in-place parsing and replacement, and will not return parsed object.
    """
    if isinstance(obj, YamlIncludeData):
        d = constructor.load(loader_type, obj)
        if nested:
            return (
                yield from yamlinclude_lazy_load(d, loader_type, constructor, nested)
            )
        else:
            return d
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = yield from yamlinclude_lazy_load(
                v, loader_type, constructor, nested
            )
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = yield from yamlinclude_lazy_load(
                v, loader_type, constructor, nested
            )
    return obj
