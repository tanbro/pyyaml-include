# How to run unit-tests

1. install the project in editable mode, and also install it's tests dependencies:

   ```bash
   cd ${workspaceFolder}
   python -m pip install -e . -r tests/requirements.txt
   ```

1. To run test cases, we can either:

   * Run tests in local/virtual-env Python environment directly

     ```bash
     cd ${workspaceFolder}
     python -m unittest
     ```

   * Run multiple python versions tests with docker compose

        ```bash
        cd ${workspaceFolder}/tests
        docker compose up
        ```
