from warnings import warn

import yaml
from yaml import (
    BaseLoader,
    # BaseDumper,
    Dumper,
    FullLoader,
    Loader,
    SafeDumper,
    SafeLoader,
    UnsafeLoader,
)

YAML_LOADERS = [BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader]
YAML_DUMPERS = [Dumper, SafeDumper]

try:
    from yaml import (
        CBaseLoader,
        # CBaseDumper,
        CDumper,
        CFullLoader,
        CLoader,
        CSafeDumper,
        CSafeLoader,
        CUnsafeLoader,
    )
except ImportError as err:
    warn(f"PyYAML was not build with libyaml: {err}")
else:
    YAML_LOADERS += [CBaseLoader, CSafeLoader, CLoader, CFullLoader, CUnsafeLoader]  # type: ignore
    YAML_DUMPERS += [CDumper, CSafeDumper]  # type: ignore

with open("tests/data/include.d/1.yaml") as f:
    YAML1 = yaml.full_load(f)
with open("tests/data/include.d/2.yaml") as f:
    YAML2 = yaml.full_load(f)
with open("tests/data/zh_cn.yaml", encoding="utf8") as f:
    YAML_ZH_CN = yaml.full_load(f)
