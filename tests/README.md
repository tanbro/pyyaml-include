# How to run unit-tests

To run test cases, we can either:

* Run tests in local/virtual-env Python environment directly

  ```bash
  cd ${workspaceFolder}
  python -m pip install -e . -r tests/requirements.txt
  python -m unittest
  ```

* Run multiple python versions tests with docker compose

  ```bash
  cd ${workspaceFolder}/tests
  docker compose up
  ```
