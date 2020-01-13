# -*- coding: utf-8 -*-

from sys import version_info
from warnings import warn

import yaml

PYTHON_VERSION_MAYOR_MINOR = '{0[0]}.{0[1]}'.format(version_info)

YAML1 = {'name': '1'}
YAML2 = {'name': '2'}
YAML_ZH_CN = {'name': u'中文'}

YAML_LOADERS = []

if '3.12' <= yaml.__version__ < '4.0':
    from yaml import BaseLoader, SafeLoader, Loader

    YAML_LOADERS = [BaseLoader, SafeLoader, Loader]
    try:
        from yaml import CBaseLoader, CSafeLoader, CLoader
    except ImportError as err:
        warn(err)
    else:
        YAML_LOADERS += [CBaseLoader, CSafeLoader, CLoader]
elif '5.0' <= yaml.__version__ < '6.0':
    from yaml import BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader

    YAML_LOADERS = [BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader]
    try:
        from yaml import CBaseLoader, CSafeLoader, CLoader, CFullLoader, CUnsafeLoader
    except ImportError as err:
        warn('{}'.format(err))
    else:
        YAML_LOADERS += [CBaseLoader, CSafeLoader, CLoader, CFullLoader, CUnsafeLoader]
else:
    raise RuntimeError('Un-supported pyyaml version: {}'.format(yaml.__version__))
