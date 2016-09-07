# QGL2 testing #

## Continuous Integration ##

The project is under continuous integration using Docker.  To test locally:

1. Build the image using the Dockerfile in test. The Dockerfile gives us
   Anaconda3, various python dependencies, and the BBN certificate installed.

    ```shell
    cd /path/to/repo/test
    docker build -t pyqgl2 .
    ```

2. Run an ephemeral container based off of the image and mount the local copy of
   the repository with changes to test.

    ```shell
    docker run -i --rm -v /path/to/repo/:/pyqgl2 pyqgl2 /bin/bash
    ```
  Or you can use the provided launch script, `launch_test_env.sh`.

3. In the container setup and run the tests

    ```shell
    export PYTHONPATH=/pyqgl2/src/python
    python -m unittest discover
    ```
