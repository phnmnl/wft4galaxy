.. _docker:

=====================
Dockerized wft4galaxy
=====================

**wft4galaxy** can also run within a Docker container, without installation.

To simplify the usage of the Docker images by command line, we provide a simple script mainly intended to allow users \
to interact with the dockerized version of the tool as if it was “native”, i.e., like a locally installed wft4galaxy.
This script is called **wft4galaxy-docker**.

**wft4galaxy-docker** supports different options; type ``wft4galaxy-docker --help`` to see all them:

.. code-block:: bash
    :name: wft4galaxy-docker-help
        :caption: wft4galaxy-docker --help

        usage: wft4galaxy-docker [-h] [--registry REGISTRY] [--repository REPO]
                                 [--version VERSION] [--image IMAGE]
                                 [--os {alpine,ubuntu}] [--skip-update]
                                 [--server SERVER] [--api-key API_KEY] [--port PORT]
                                 [--volume VOLUME] [--debug]
                                 {jupyter,runtest,generate-test,ipython,generate-template,bash}
                                 ...

        optional arguments:
          -h, --help            show this help message and exit
          --registry REGISTRY   Alternative Docker registry (default is "DockerHub")
          --repository REPO     Alternative Docker repository containing the "wft4galaxy" Docker image (default is "crs4")
          --version VERSION     Alternative version of the "wft4galaxy" Docker image(default is "develop")
          --image IMAGE         Alternative "wft4galaxy" Docker image name specified as NAME:TAG
          --os {alpine,ubuntu}  Base OS of the Docker image (default is "alpine" and it is ignored when the "--image" option is specified)
          --skip-update         Skip the update of the "wft4galaxy" Docker image and use the local version if it is available
          --server SERVER       Galaxy server URL
          --api-key API_KEY     Galaxy server API KEY
          --port PORT           Docker port to expose
          --volume VOLUME       Docker volume to mount
          --debug               Enable debug mode

        Container entrypoint:
          Available entrypoints for the 'wft4galaxy' Docker image.

          {jupyter,runtest,generate-test,ipython,generate-template,bash}
                                Choose one of the following options:
            jupyter             Execute the "Jupyter" server as entrypoint
            runtest             Execute the "wft4galaxy" tool as entrypoint (default)
            generate-test       Execute the "generate-test" wizard command as entrypoint
            ipython             Execute the "Ipython" shell as entrypoint
            generate-template   Execute the "generate-template" wizard command as entrypoint
            bash                Execute the "Bash" shell as entrypoint



**Which Galaxy?**

You specify which Galaxy instance ``wft4galaxy-docker`` should use by setting these two environment variables  \
which are automagically injected on Docker containers:

.. code-block:: bash

    GALAXY_URL                   Galaxy URL
    GALAXY_API_KEY               User API key

You can override this behaviour from the command line with these switches:

.. code-block:: bash

      --server  SERVER       Galaxy server URL
      --api-key API_KEY      Galaxy server API KEY


-----------
Basic Usage
-----------

As a first basic use case, \
you can use ``wft4galaxy-docker`` to launch your Galaxy workflow tests just as you would with the ``wft4galaxy`` script \
provided by native installation of **wft4galaxy** (see ":ref:`installation`" section).
This corresponds to launch ``wft4galaxy-docker`` with the argument ``runtest``, which is its default execution mode.

Thus, you can run all the tests defined in a workflow test suite definition file, \
like ``examples/workflow-testsuite-conf.yml`` (see ":ref:`notebooks/1_define_test_suite.ipynb`" and \
":ref:`test_definition_file`" for more details), by simply typing:


.. code-block:: bash
   :name: wft4galaxy-docker-runtest

   wft4galaxy-docker runtest -f examples/workflow-testsuite-conf.yml


Being the default command, `runtest` can be omitted:

.. code-block:: bash
   :name: wft4galaxy-docker-runtest-omitted

   wft4galaxy-docker -f examples/workflow-testsuite-conf.yml


That is, the same syntax supported by the ``wft4galaxy`` script (see ":ref:`notebooks/0_basic_usage.ipynb`").

The other basic two use cases for ``wft4galaxy-docker`` deal with the *wizard* feature \
that wft4galaxy provides (see :ref:`wizard_tool`). For example, you can generate a test-suite template folder:

.. code-block:: bash
   :name: wft4galaxy-docker-generate-template

   wft4galaxy-docker -o MyTestSuite generate-template


or generate a test from a Galaxy history:

.. code-block:: bash
   :name: wft4galaxy-docker-generate-test

   wft4galaxy-docker -o MyTestSuite generate-test MyHistoryName



-----------------------------
Development Usage
-----------------------------

The ``wft4galaxy-docker`` script also provides several advanced usage commands mainly intended for development purposes.
They provide you a development environment with wft4galaxy already installed, configured and
ready to use running within a Docker container, where you can interact with wft4galaxy
either via its main `wft4galaxy` command (see :ref:`notebooks/0_basic_usage.ipynb`)
or programmatically, using its API (see :ref:`api`).

Specifically, the dockerized development environments are:

===========================   =============================
Environment                   wft4galaxy-docker CMD
===========================   =============================
BASH shell                    ``wft4galaxy-docker bash``
ipython interpreter           ``wft4galaxy-docker ipython``
jupyter notebook server       ``wft4galaxy-docker jupyter``
===========================   =============================


.. note:: The default port of the jupyter notebook server is **9876**: \
          use ``--web-port`` to change it.



^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Customized container instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**wft4galaxy-docker** allows to customize your running container set-up with a Docker-like syntax:

===========================   ================================================
mount a volume                ``-volume myhost-folder:/container-host-folder``
expose a port                 ``--port 8888:80``
===========================   ================================================


^^^^^^^^^^^^^^^^^^
Customized images
^^^^^^^^^^^^^^^^^^

The wft4galaxy Docker images officially supported are based on Alpine and Ubuntu Linux.
The two versions are equivalent since they have the same set of packages installed.
But the ``alpine`` linux version is used by default due to its smaller size (~250 MB),
about the half of the equivalent based on ubuntu (~548.3 MB).
You can use the option ``--os [alpine|ubuntu]`` to choose which use.


You can also build your custom Docker image and tell ``wft4galaxy-docker`` how to pull it by using the options:

.. code-block:: bash

   --registry REGISTRY   Alternative Docker registry (default is "DockerHub")
   --repository REPO     Alternative Docker repository containing the "wft4galaxy" Docker image (default is "crs4")
   --version VERSION     Alternative version of the "wft4galaxy" Docker image(default is "develop")
   --image IMAGE         Alternative "wft4galaxy" Docker image name specified as NAME:TAG


.. note:: When you launch ``wft4galaxy-docker``, by default it tries to pull the latest version    \
          of Docker image it requires. To avoid this behaviour we can launch it with the option ``--skip-update`` \
          which forces the use of your local available version of the required Docker image.



-------------------
Direct Docker Usage
-------------------

For a direct Docker usage the following syntax holds:

.. code-block:: bash

  docker run -it --rm [DOCKER_OPTIONS] crs4/wft4galaxy[-develop]:[alpine|ubuntu]-develop \
                      <ENTRYPOINT> [ENTRYPOINT_OPTIONS]

.. note:: When using ``docker`` directly you will need to explicitly mount the volumes that are required \
          to read the configuration file of your suite and to write results.


.. toctree::
   :hidden:

    Example <notebooks/6_direct_docker_usage.ipynb>

You can find an example :ref:`here <notebooks/6_direct_docker_usage.ipynb>`.
