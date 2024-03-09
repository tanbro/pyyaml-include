# How to run unit-tests

1. install the project in editable mode, and also install it's development dependencies:

   ```bash
   cd ${workspaceFolder}
   python -m pip install -r requirements.txt
   ```

1. To run test cases, we can either:

   * Run tests in local/virtual-env Python environment directly

     ```bash
     cd ${workspaceFolder}
     python -m unittest
     ```

   or:

   * Run multiple python version test in docker:

     1. Build the project's package:

        ```bash
        python -m build
        ```

     1. Run multiple python versions tests with docker compose

        ```bash
        cd tests
        docker compose up
        ```
