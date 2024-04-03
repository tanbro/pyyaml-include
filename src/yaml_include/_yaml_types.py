from typing import Type

import yaml


if yaml.__with_libyaml__:
    type TYamlLoaders = (  # type: ignore
        yaml.BaseLoader
        | yaml.FullLoader
        | yaml.Loader
        | yaml.SafeLoader
        | yaml.UnsafeLoader
        | yaml.CBaseLoader
        | yaml.CFullLoader
        | yaml.CLoader
        | yaml.CSafeLoader
        | yaml.CUnsafeLoader
    )
    type TYamlDumpers = (  # type: ignore
        yaml.BaseDumper | yaml.Dumper | yaml.SafeDumper | yaml.CBaseDumper | yaml.CDumper | yaml.CSafeDumper
    )
    type TYamlLoaderTypes = (  # type: ignore
        Type[yaml.BaseLoader]
        | Type[yaml.FullLoader]
        | Type[yaml.Loader]
        | Type[yaml.SafeLoader]
        | Type[yaml.UnsafeLoader]
        | Type[yaml.CBaseLoader]
        | Type[yaml.CFullLoader]
        | Type[yaml.CLoader]
        | Type[yaml.CSafeLoader]
        | Type[yaml.CUnsafeLoader]
    )
    type TYamlDumperTypes = (  # type: ignore
        Type[yaml.BaseDumper]
        | Type[yaml.Dumper]
        | Type[yaml.SafeDumper]
        | Type[yaml.CBaseDumper]
        | Type[yaml.CDumper]
        | Type[yaml.CSafeDumper]
    )
else:
    type TYamlLoaders = (  # type: ignore
        yaml.BaseLoader | yaml.FullLoader | yaml.Loader | yaml.SafeLoader | yaml.UnsafeLoader
    )
    type TYamlDumpers = (  # type: ignore
        yaml.BaseDumper | yaml.Dumper | yaml.SafeDumper
    )
    type TYamlLoaderTypes = (  # type: ignore
        Type[yaml.BaseLoader] | Type[yaml.FullLoader] | Type[yaml.Loader] | Type[yaml.SafeLoader] | Type[yaml.UnsafeLoader]
    )
    type TYamlDumperTypes = (  # type: ignore
        Type[yaml.BaseDumper] | Type[yaml.Dumper] | Type[yaml.SafeDumper]
    )
