# QGL2 testing #

## Continuous Integration ##

The project is under continuous integration using Docker.  To test locally:

1. Build the image using the Dockerfile in test. The Dockerfile gives us
   Anaconda3, various python dependencies, and the BBN certificate installed.

    ```shell
    cd /path/to/repo/test
    docker build -t pyqgl2 .
    ```

1. Run an ephemeral container based off of the image and mount the local copy of
   the repository with changes to test.

    ```shell
    docker run -it --rm -v /path/to/repo/:/pyqgl2 pyqgl2 /bin/bash
    ```

1. In the container setup and run the tests

    ```shell
    export PYTHONPATH=/pyqgl2/
    python -m unittest discover
    ```
