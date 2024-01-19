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

## Usage

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

To include `1.yml`, `2.yml` in `0.yml`, we shall add `YamlInclude` to [PyYAML]'s loader, then add an `!inc` tag in `0.yaml`:

```python
import yaml
from yamlinclude import YamlInclude

# add the tag
yaml.add_constructor(
    tag="!inc",
    constructor=YamlInclude(base_dir='/your/conf/dir'),
    Loader=yaml.Loader
)

with open('0.yml') as f:
    data = yaml.load(f, Loader=yaml.Loader)

print(data)

# remove the tag
del yaml.Loader.yaml_constructors["!inc"]
```

### Include in Mapping

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

### Include in Sequence

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

### Wildcards

File name can contain shell-style wildcards. Data loaded from the file(s) found by wildcards will be set in a sequence.

That is to say, a list will be returned when including file name contains wildcards.
Length of the returned list equals number of matched files:

- when only 1 file matched, length of list will be 1
- when there are no files matched, an empty list will be returned

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

## fsspec

From `v2.0`, yamlinclude use [fsspec][] to open including files.

[fsspec][] makes it possible to include file from many different sources, as local file system, S3, HTTP, SFTP, etc ...

[YAML]: http://yaml.org/
[PyYaml]: https://pypi.org/project/PyYAML/
[fsspec]: https://github.com/fsspec/filesystem_spec/ "Filesystem Spec (fsspec) is a project to provide a unified pythonic interface to local, remote and embedded file systems and bytes storage."
