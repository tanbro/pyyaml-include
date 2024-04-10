from warnings import warn

import yaml
from yaml import (
    BaseLoader,
    FullLoader,
    Loader,
    SafeLoader,
    UnsafeLoader,
    # BaseDumper,
    Dumper,
    SafeDumper,
)

YAML_LOADERS = [BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader]
YAML_DUMPERS = [Dumper, SafeDumper]

try:
    from yaml import (
        CBaseLoader,
        CFullLoader,
        CLoader,
        CSafeLoader,
        CUnsafeLoader,
        # CBaseDumper,
        CDumper,
        CSafeDumper,
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
