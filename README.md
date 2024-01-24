# pyyaml-include

[![GitHub tag](https://img.shields.io/github/tag/tanbro/pyyaml-include.svg)](https://github.com/tanbro/pyyaml-include)
[![Python Package](https://github.com/tanbro/pyyaml-include/workflows/Python%20package/badge.svg)](https://github.com/tanbro/pyyaml-include/actions?query=workflow%3A%22Python+package%22)
[![Documentation Status](https://readthedocs.org/projects/pyyaml-include/badge/?version=latest)](https://pyyaml-include.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=tanbro_pyyaml-include&metric=alert_status)](https://sonarcloud.io/dashboard?id=tanbro_pyyaml-include)

An extending constructor of [PyYAML][]: include other [YAML][] files into [YAML][] document.

## Install

```sh
pip install "pyyaml-include>=2.0"
```

## Basic usages

Consider we have such [YAML] files:

```text
├── 0.yml
└── include.d
    ├── 1.yml
    └── 2.yml
```

- `1.yml` 's content:

  ```yaml
  name: "1"
  ```

- `2.yml` 's content:

  ```yaml
  name: "2"
  ```

To include `1.yml`, `2.yml` in `0.yml`, we shall:

1. add `YamlInclude` to [PyYAML]'s loader, then write an `!inc` tag in `0.yaml`:

   ```python
   import yaml
   from yamlinclude import YamlInclude

   # add the tag
   yaml.add_constructor(
      tag="!inc",
      constructor=YamlInclude(base_dir='/your/conf/dir'),
      Loader=yaml.Loader
   )
   ```

1. write `!inc` tags in `0.yaml`:

   ```yaml
   file1: !inc include.d/1.yml
   file2: !inc include.d/1.yml
   ```

1. load it

   ```python
   with open('0.yml') as f:
      data = yaml.load(f, Loader=yaml.Loader)
   print(data)
   ```

   we'll get:

   ```json
   "file1":  {
       "name": "1"
   },
   "file2":  {
       "name": "2"
   },
   ```

1. the constructor can be removed:

   ```yml
   del yaml.Loader.yaml_constructors["!inc"]
   ```

### In Mapping

If `0.yml` was:

```yaml
file1: !inc include.d/1.yml
file2: !inc include.d/2.yml
```

We'll get:

```yaml
file1:
  name: "1"
file2:
  name: "2"
```

### In Sequence

If `0.yml` was:

```yaml
files:
  - !inc include.d/1.yml
  - !inc include.d/2.yml
```

We'll get:

```yaml
files:
  - name: "1"
  - name: "2"
```

## Advanced usages

### Wildcards

File name can contain shell-style wildcards. Data loaded from the file(s) found by wildcards will be set in a sequence.

That is to say, a list will be returned when including file name contains wildcards.
Length of the returned list equals number of matched files:

- when only 1 file matched, length of list will be 1
- when there are no files matched, an empty list will be returned

We support `**`, `?` and `[..]`. We do not support `^` for pattern negation.
The `maxdepth` option is applied on the first `**` found in the path.

> ℹ **Note**
>
> Using the `**` pattern in large directory trees or remote file system (S3, HTTP ...) may consume an inordinate amount of time.

If `0.yml` was:

```yaml
files: !inc include.d/*.yml
```

We'll get:

```yaml
files:
  - name: "1"
  - name: "2"
```

### Work with fsspec

In `v2.0`, we use [fsspec][] to open including files, which makes it possible to include file from many different sources, such as local file system, S3, HTTP, SFTP ...

For example, we can include a file from a website in YAML:

```yaml
conf:
  logging: !inc http://domain/etc/app/conf.d/logging.yml
```

In such situations, when creating a `yamlinclude` constructor, a [fsspec][] filesystem object shall be set to `fs` argument.

For example, if want to include files from a website, we shall:

1. create a YAML-Include tag constructor, with a [fsspec][] HTTP filesystem object as it's `fs`:

   ```python
   import yaml
   import fsspec
   from yamlinclude import YamlInclude

   http_fs = fsspec.filesystem(
      "http", client_kwargs=dict(base_url=f"http://{HOST}:{PORT}")
   )

   ctor = YamlInclude(http_fs, base_dir="/foo/baz")
   yaml.add_constructor("!inc", ctor, yaml.Loader)
   ```

1. then, write a [YAML][] document to include files from `http://${HOST}:${PORT}`:

   ```yaml
   key1: !inc doc1.yml    # relative path to "base_dir"
   key2: !inc ./doc2.yml  # relative path to "base_dir" also
   key3: !inc /doc3.yml   # absolute path, "base_dir" does not affect
   key3: !inc ../doc4.yml # relative path one level upper to "base_dir"
   ```

1. load it with `PyYAML`:

   ```python
   yaml.load(yaml_string, yaml.Loader)
   ```

Above [YAML][] snippet will be loaded as:

- `key1`: pared YAML of `http://${HOST}:${PORT}/foo/baz/doc1.yml`
- `key2`: pared YAML of `http://${HOST}:${PORT}/foo/baz/doc2.yml`
- `key3`: pared YAML of `http://${HOST}:${PORT}/doc3.yml`
- `key4`: pared YAML of `http://${HOST}:${PORT}/foo/doc4.yml`

> 💡 **Tips**
>
> Check [fsspec][]'s documentation for more

> 💡 **Note**
>
> If `fs` argument is omitted or `None`, a `"file"`/`"local"` [fsspec][] filesystem object will be used. That is to say:
>
> ```yaml
> data: !inc: foo/baz.yaml
> ```
>
> is equivalent to (if no `base_dir` was set in `YamlInclude()`):
>
> ```yaml
> data: !inc: file://foo/baz.yaml
> ```
>
> and
>
> ```python
> yaml.add_constructor("!inc", YamlInclude())
> ```
>
> is equivalent to:
>
> ```python
> yaml.add_constructor("!inc", YamlInclude(fs=fsspec.filesystem("file")))
> ```

### The base_dir argument

- If `base_dir` is omitted or `None`, the actually including file path is the path in defined in [YAML][] without a change, and different [fsspec][] filesystem will treat them differently. For a local filesystem, it will be `CWD`.

[YAML]: http://yaml.org/ "YAML: YAML Ain't Markup Language™"
[PyYaml]: https://pypi.org/project/PyYAML/ "PyYAML is a full-featured YAML framework for the Python programming language."
[fsspec]: https://github.com/fsspec/filesystem_spec/ "Filesystem Spec (fsspec) is a project to provide a unified pythonic interface to local, remote and embedded file systems and bytes storage."
