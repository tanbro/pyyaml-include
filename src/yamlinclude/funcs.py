# from typing import Any, Mapping, Optional, Sequence

# import yaml

# from .data import YamlIncludeData


# def yaml_include(
#     obj,
#     loader_type,
#     *,
#     base_dir: Optional[str] = None,
#     inplace: bool = False,
# ):
#     if isinstance(obj, YamlIncludeData):
#         tpl = env.from_string(obj.source) if env else jinja2.Template(obj.source)
#         s = tpl.render(**(context or dict()))
#         d = yaml.load(s, obj.loader_type)
#         return yaml_include(d)
#     elif isinstance(obj, Mapping):
#         if inplace:
#             for k, v in obj.items():
#                 obj[k] = extract(v, env, context, inplace=True)  # type: ignore
#         else:
#             return {
#                 k: yaml_include(v, env, context, inplace=False) for k, v in obj.items()
#             }
#     elif isinstance(obj, Sequence) and not isinstance(
#         obj, (bytearray, bytes, memoryview, str)
#     ):
#         if inplace:
#             for i, v in enumerate(obj):
#                 obj[i] = extract(v, env, context, inplace=True)  # type: ignore
#         else:
#             return [yaml_include(m, env, context, inplace=False) for m in obj]
#     return obj
