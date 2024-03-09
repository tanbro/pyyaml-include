import sys
from typing import Any, Generator, Mapping, MutableMapping, MutableSequence, Sequence


if sys.version_info < (3, 12):
    from .yamltypes_backward import TYamlLoaderTypes
else:
    from .yamltypes import TYamlLoaderTypes

from .constructor import YamlIncludeCtor
from .data import YamlIncludeData
from .utils import load

__all__ = ["load_yaml_include", "iload_yaml_include"]


def load_yaml_include(
    obj: Any,
    loader_type: TYamlLoaderTypes,
    constructor: YamlIncludeCtor,
    inplace: bool = False,
    nested: bool = False,
) -> Any:
    """Recursively load :class:`YamlIncludeCtor` tag objects in a YAML doc-tree."""
    if isinstance(obj, YamlIncludeData):
        d = load(loader_type, constructor, obj)
        if nested:
            return load_yaml_include(d, loader_type, constructor, inplace, nested)
        else:
            return d
    elif isinstance(obj, Mapping):
        if inplace:
            assert isinstance(obj, MutableMapping)
            for k, v in obj.items():
                obj[k] = load_yaml_include(v, loader_type, constructor, inplace, nested)
        else:
            return {k: load_yaml_include(v, loader_type, constructor, inplace, nested) for k, v in obj.items()}
    elif isinstance(obj, Sequence) and not isinstance(obj, (bytearray, bytes, memoryview, str)):
        if inplace:
            assert isinstance(obj, MutableSequence)
            for i, v in enumerate(obj):
                obj[i] = load_yaml_include(v, loader_type, constructor, inplace, nested)
        else:
            return [load_yaml_include(m, loader_type, constructor, inplace, nested) for m in obj]
    return obj


def iload_yaml_include(
    obj: Any,
    loader_type: TYamlLoaderTypes,
    constructor: YamlIncludeCtor,
    nested: bool = False,
) -> Generator[None, None, Any]:
    if isinstance(obj, YamlIncludeData):
        d = load(loader_type, constructor, obj)
        if nested:
            return (yield from iload_yaml_include(d, loader_type, constructor, nested))
        else:
            return d
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = yield from iload_yaml_include(v, loader_type, constructor, nested)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = yield from iload_yaml_include(v, loader_type, constructor, nested)
    return obj
