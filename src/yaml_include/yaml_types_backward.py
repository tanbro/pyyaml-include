import sys

if not sys.version_info < (3, 12):
    raise ImportError("Python greater than or equal to 3.12 should “import yamltypes”")

from typing import Type, Union

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

import yaml

if yaml.__with_libyaml__:
    TYamlLoaders: TypeAlias = Union[  # type: ignore
        yaml.BaseLoader,
        yaml.FullLoader,
        yaml.Loader,
        yaml.SafeLoader,
        yaml.UnsafeLoader,
        yaml.CBaseLoader,
        yaml.CFullLoader,
        yaml.CLoader,
        yaml.CSafeLoader,
        yaml.CUnsafeLoader,
    ]
    TYamlDumpers: TypeAlias = Union[  # type: ignore
        yaml.BaseDumper,
        yaml.Dumper,
        yaml.SafeDumper,
        yaml.CBaseDumper,
        yaml.CDumper,
        yaml.CSafeDumper,
    ]
    TYamlLoaderTypes: TypeAlias = Union[  # type: ignore
        Type[yaml.BaseLoader],
        Type[yaml.FullLoader],
        Type[yaml.Loader],
        Type[yaml.SafeLoader],
        Type[yaml.UnsafeLoader],
        Type[yaml.CBaseLoader],
        Type[yaml.CFullLoader],
        Type[yaml.CLoader],
        Type[yaml.CSafeLoader],
        Type[yaml.CUnsafeLoader],
    ]
    TYamlDumperTypes: TypeAlias = Union[  # type: ignore
        Type[yaml.BaseDumper],
        Type[yaml.Dumper],
        Type[yaml.SafeDumper],
        Type[yaml.CBaseDumper],
        Type[yaml.CDumper],
        Type[yaml.CSafeDumper],
    ]
else:
    TYamlLoaders: TypeAlias = Union[  # type: ignore
        yaml.BaseLoader,
        yaml.FullLoader,
        yaml.Loader,
        yaml.SafeLoader,
        yaml.UnsafeLoader,
    ]
    TYamlDumpers: TypeAlias = Union[yaml.BaseDumper, yaml.Dumper, yaml.SafeDumper]  # type: ignore
    TYamlLoaderTypes: TypeAlias = Union[  # type: ignore
        Type[yaml.BaseLoader],
        Type[yaml.FullLoader],
        Type[yaml.Loader],
        Type[yaml.SafeLoader],
        Type[yaml.UnsafeLoader],
    ]
    TYamlDumperTypes: TypeAlias = Union[Type[yaml.BaseDumper], Type[yaml.Dumper], Type[yaml.SafeDumper]]  # type: ignore
