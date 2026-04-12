# pyyaml-include

[![GitHub tag](https://img.shields.io/github/tag/tanbro/pyyaml-include.svg)](https://github.com/tanbro/pyyaml-include)
[![Python Package](https://github.com/tanbro/pyyaml-include/workflows/Python%20package/badge.svg)](https://github.com/tanbro/pyyaml-include/actions?query=workflow%3A%22Python+package%22)
[![Documentation Status](https://readthedocs.org/projects/pyyaml-include/badge/?version=latest)](https://pyyaml-include.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![codecov](https://codecov.io/gh/tanbro/pyyaml-include/graph/badge.svg?token=N4QBGv08EE)](https://codecov.io/gh/tanbro/pyyaml-include)

> Include other YAML files into your YAML documents

**pyyaml-include** extends PyYAML with a simple, powerful include mechanism. Support local files, HTTP, S3, SFTP, and more through [fsspec][].

---

## Quick Start

```bash
pip install "pyyaml-include"
```

```python
# main.py
import yaml
import yaml_include

# Register the include tag
yaml.add_constructor("!inc", yaml_include.Constructor())

# Load YAML with includes
with open("config.yml") as f:
    config = yaml.full_load(f)
```

```yaml
# config.yml
database: !inc config/database.yml
features: !inc config/features/*.yml
```

That's it! Your YAML files are now merged together.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Why pyyaml-include?](#why-pyyaml-include)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
  - [Include Single File](#include-single-file)
  - [Include Multiple Files](#include-multiple-files)
  - [Nested Includes](#nested-includes)
- [Advanced Usage](#advanced-usage)
  - [Remote Files (HTTP, S3, SFTP)](#remote-files-http-s3-sftp)
  - [Custom File Formats (JSON, TOML)](#custom-file-formats-json-toml)
  - [Serialization Support](#serialization-support)
  - [Wildcard Patterns](#wildcard-patterns)
- [Reference](#reference)
  - [Constructor Options](#constructor-options)
  - [YAML Tag Parameters](#yaml-tag-parameters)
  - [Path Resolution](#path-resolution)
- [Migration Guide](#migration-guide)

---

## Why pyyaml-include?

| Feature              | Description                                        |
| -------------------- | -------------------------------------------------- |
| **Simple**           | Just add `!inc` tag to your YAML                   |
| **Flexible**         | Include local files, HTTP, S3, SFTP, and more      |
| **Powerful**         | Wildcard patterns, nested includes, custom loaders |
| **Production-ready** | Comprehensive tests, type hints, documentation     |

---

## Installation

### Basic Installation

```bash
pip install "pyyaml-include"
```

### With Remote File Support

```bash
# HTTP/HTTPS files
pip install "pyyaml-include" fsspec[http]

# S3 files
pip install "pyyaml-include" fsspec[s3]

# SFTP files
pip install "pyyaml-include" fsspec[sftp]

# Multiple sources
pip install "pyyaml-include" fsspec[http,s3,sftp]
```

See [fsspec documentation](https://filesystem-spec.readthedocs.io/) for all supported filesystems.

---

## Basic Usage

### Include Single File

**Directory structure:**
```
config/
├── main.yml
└── database.yml
```

**config/database.yml:**
```yaml
host: localhost
port: 5432
name: mydb
```

**config/main.yml:**
```yaml
database: !inc database.yml
app:
  name: MyApp
```

**Result:**
```python
{
    'database': {'host': 'localhost', 'port': 5432, 'name': 'mydb'},
    'app': {'name': 'MyApp'}
}
```

### Include Multiple Files

**Directory structure:**
```
config/
├── main.yml
└── features/
    ├── auth.yml
    ├── payment.yml
    └── notification.yml
```

**config/main.yml:**
```yaml
features: !inc features/*.yml
```

**Result:**
```yaml
features:
  - # contents of auth.yml
  - # contents of payment.yml
  - # contents of notification.yml
```

### Nested Includes

**config/main.yml:**
```yaml
base: !inc base.yml
environment:
  production: !inc env/production.yml
  development: !inc env/development.yml
```

**config/env/production.yml:**
```yaml
database: !inc database/production.yml
```

Nested includes work automatically - no additional configuration needed.

---

## Advanced Usage

### Remote Files (HTTP, S3, SFTP)

**HTTP Example:**

```python
import yaml
import fsspec
import yaml_include

# Create HTTP filesystem
http_fs = fsspec.filesystem(
    "http",
    client_kwargs={"base_url": "https://example.com"}
)

# Register with HTTP filesystem
yaml.add_constructor(
    "!inc",
    yaml_include.Constructor(fs=http_fs, base_dir="/config"),
    yaml.Loader
)
```

```yaml
# Your YAML
logging: !inc logging.yml
database: !inc database/production.yml
```

**S3 Example:**

```python
s3_fs = fsspec.filesystem("s3", key="YOUR_KEY", secret="YOUR_SECRET")
yaml.add_constructor(
    "!inc",
    yaml_include.Constructor(fs=s3_fs, base_dir="my-bucket/config"),
    yaml.Loader
)
```

```yaml
# Load from S3
config: !inc app-settings.yml
```

### Custom File Formats (JSON, TOML)

You can include non-YAML files using a custom loader:

```python
import json
import tomllib as toml
import yaml
import yaml_include

def custom_loader(urlpath, file, Loader):
    """Load JSON, TOML, or YAML files."""
    if urlpath.endswith(".json"):
        return json.load(file)
    if urlpath.endswith(".toml"):
        return toml.load(file)
    # Default to YAML
    return yaml.load(file, Loader)

# Create constructor with custom loader
ctor = yaml_include.Constructor(custom_loader=custom_loader)
yaml.add_constructor("!inc", ctor, yaml.Loader)
```

```yaml
# Now you can include JSON and TOML files
package_json: !inc package.json
config_toml: !inc pyproject.toml
config_yaml: !inc settings.yml
```

### Serialization Support

To preserve include statements when dumping YAML:

```python
import yaml
import yaml_include

# Create constructor without auto-loading
ctor = yaml_include.Constructor(autoload=False)
yaml.add_constructor("!inc", ctor)

# Add representer for serialization
rpr = yaml_include.Representer("inc")
yaml.add_representer(yaml_include.Data, rpr)

# Load without resolving includes
data = yaml.load(yaml_string, yaml.Loader)
# data contains yaml_include.Data objects, not loaded content

# Serialize (preserves !inc tags)
yaml_str = yaml.dump(data)

# Load and resolve includes
ctor.autoload = True
loaded = yaml.load(yaml_str, yaml.Loader)
```

### Wildcard Patterns

Supported wildcards (shell-style):

| Pattern | Matches                    |
| ------- | -------------------------- |
| `*`     | Any characters             |
| `?`     | Single character           |
| `[abc]` | One of a, b, or c          |
| `**`    | Recursive directory search |

```yaml
# All YAML files in directory
files: !inc config/*.yml

# All YAML files recursively
all_files: !inc config/**/*.yml

# Files matching pattern
specific: !inc logs/app-*.yml
```

> ⚠️ **Warning:** Using `**` in large directories or remote filesystems can be slow. All matched files are loaded into memory.

---

## Limitations

### Merge Keys and Anchors

**⚠️ Merge keys (`<<`) and anchors (`&`/`*) don't work with include tags.**

This is a fundamental limitation of PyYAML's architecture - merge key and anchor validation happens before custom tags are processed.

**Instead of this (won't work):**
```yaml
<<: !inc config/base.yml
```

**Use one of these alternatives:**

1. **Include separately, then merge in Python:**
   ```yaml
   base: !inc config/base.yml
   override: !inc config/override.yml
   ```
   ```python
   config = yaml.load(yaml_string)
   merged = {**config['base'], **config['override']}
   ```

2. **Use wildcard includes for multiple files:**
   ```yaml
   configs: !inc config.d/*.yml  # Returns a list
   ```
   ```python
   config = yaml.load(yaml_string)
   # Merge all configs
   merged = {}
   for cfg in config['configs']:
       merged.update(cfg)
   ```

See [issues #45](https://github.com/tanbro/pyyaml-include/issues/45) and [#53](https://github.com/tanbro/pyyaml-include/issues/53) for more details.

---

## Reference

### Constructor Options

```python
yaml_include.Constructor(
    fs=None,           # fsspec filesystem (default: local filesystem)
    base_dir=None,     # Base directory for relative paths
    autoload=True,     # Auto-load included files (False returns Data objects)
    custom_loader=None # Custom loader function for non-YAML files
)
```

**Example:**

```python
# Local files with base directory
yaml.add_constructor(
    "!inc",
    yaml_include.Constructor(base_dir="/path/to/config")
)

# HTTP remote files
http_fs = fsspec.filesystem("http", client_kwargs={"base_url": "https://example.com"})
yaml.add_constructor(
    "!inc",
    yaml_include.Constructor(fs=http_fs, base_dir="/config")
)

# Without auto-loading (for serialization)
yaml.add_constructor(
    "!inc",
    yaml_include.Constructor(autoload=False)
)
```

### YAML Tag Parameters

The `!inc` tag supports multiple parameter formats:

**Simple string (most common):**
```yaml
files: !inc config/*.yml
```

**Sequence (positional parameters):**
```yaml
# With encoding
files: !inc ["config/*.yml", {encoding: utf-8}]

# With maxdepth for recursive search
files: !inc ["config/**/*.yml", {maxdepth: !!int "2"}]

# Both glob and open parameters
files: !inc ["config/**/*.yml", {maxdepth: !!int "2"}, {encoding: utf-16}]
```

**Mapping (named parameters):**
```yaml
files: !inc {urlpath: config/*.yml, encoding: utf-8}
```

#### Parameter Passing Details

How parameters are passed depends on the URL pattern:

| URL Pattern           | Has Wildcard | Has Scheme | Behavior                             |
| --------------------- | ------------ | ---------- | ------------------------------------ |
| `file.yml`            | No           | No         | `fs.open(path)`                      |
| `*.yml`               | Yes          | No         | `fs.glob()` → `fs.open()` for each   |
| `http://.../file.yml` | No           | Yes        | `fsspec.open()` (ignores `fs`)       |
| `http://.../*.yml`    | Yes          | Yes        | `fsspec.open_files()` (ignores `fs`) |

<details>
<summary>Advanced: Separate glob and open parameters</summary>

When using wildcards without a scheme, you can specify separate parameters for `glob` and `open`:

```yaml
# Mapping form
files: !inc {urlpath: "config/**/*.yml", glob: {maxdepth: 2}, open: {encoding: utf-16}}

# Sequence form
files: !inc ["config/**/*.yml", {maxdepth: !!int "2"}, {encoding: utf-16}]
```

</details>

### Path Resolution

**Relative paths** are resolved relative to `base_dir`:

```python
yaml.add_constructor(
    "!inc",
    yaml_include.Constructor(base_dir="/app/config")
)
```

```yaml
# Loads /app/config/database.yml
db: !inc database.yml

# Loads /app/config/sub/settings.yml
settings: !inc sub/settings.yml

# Absolute path - base_dir is ignored
absolute: !inc /other/path/file.yml
```

**Without `base_dir`:** Relative paths use the current working directory (for local filesystem) or may fail (for remote filesystems).

**Full URLs** (with scheme) ignore `base_dir`:

```yaml
# base_dir is ignored for full URLs
remote: !inc https://example.com/config.yml
```

---

## Migration Guide

### Upgrading from v1.x to v2.x

> ⚠️ **Breaking Change:** Version 2.0 is **NOT** compatible with 1.0

**Key changes:**

1. **fsspec integration:** All file operations now use fsspec
2. **Parameter passing:** New parameter syntax for advanced use cases
3. **Wildcard behavior:** Improved wildcard support with glob patterns

**Basic usage remains the same:**
```python
# This still works
yaml.add_constructor("!inc", yaml_include.Constructor())
```

**Advanced usage requires updates:**
```python
# v1.x
yaml.add_constructor("!inc", yaml_include.Constructor(base_dir='/path'))

# v2.x - same, but with fsspec backend
yaml.add_constructor("!inc", yaml_include.Constructor(base_dir='/path'))
# fs defaults to fsspec.filesystem("file")
```

See [full documentation](https://pyyaml-include.readthedocs.io/) for detailed migration notes.

---

## Links

- **Documentation:** [pyyaml-include.readthedocs.io](https://pyyaml-include.readthedocs.io/)
- **GitHub:** [github.com/tanbro/pyyaml-include](https://github.com/tanbro/pyyaml-include)
- **PyPI:** [pypi.org/project/pyyaml-include](https://pypi.org/project/pyyaml-include/)

---

## License

GPL-3.0-or-later

---

[YAML]: http://yaml.org/
[PyYAML]: https://pypi.org/project/PyYAML/
[fsspec]: https://github.com/fsspec/filesystem_spec/
