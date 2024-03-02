from warnings import warn

import yaml
from yaml import BaseLoader, FullLoader, Loader, SafeLoader, UnsafeLoader

YAML_LOADERS = [BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader]

try:
    from yaml import CBaseLoader, CFullLoader, CLoader, CSafeLoader, CUnsafeLoader
except ImportError as err:
    warn(f"PyYAML was not build with libyaml: {err}")
else:
    YAML_LOADERS += [CBaseLoader, CSafeLoader, CLoader, CFullLoader, CUnsafeLoader]

with open("tests/data/include.d/1.yaml") as f:
    YAML1 = yaml.full_load(f)
with open("tests/data/include.d/2.yaml") as f:
    YAML2 = yaml.full_load(f)
with open("tests/data/zh_cn.yaml") as f:
    YAML_ZH_CN = yaml.full_load(f)
