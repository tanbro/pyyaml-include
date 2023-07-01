from warnings import warn

from yaml import BaseLoader, FullLoader, Loader, SafeLoader, UnsafeLoader

YAML_LOADERS = [BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader]
try:
    from yaml import CBaseLoader, CFullLoader, CLoader, CSafeLoader, CUnsafeLoader
except ImportError as err:
    warn(f"PyYAML was not build with libyaml: {err}")
else:
    YAML_LOADERS += [CBaseLoader, CSafeLoader, CLoader, CFullLoader, CUnsafeLoader]

YAML1 = {"name": "1"}
YAML2 = {"name": "2"}
YAML_ZH_CN = {"name": "中文"}
