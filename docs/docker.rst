.. _docker:

=====================
Dockerized wft4galaxy
=====================

**wft4galaxy** can also run within a Docker container.

To simplify the usage of the Docker images by command line, we provide a simple bash script mainly intended to allow users to interact with the dockerized version of the tool as it was "native", i.e., like the not dockerized ``wft4galaxy``. Such a script is named ``wft4galaxy-docker``.

Installation
============

To download and install the ``wft4galaxy-docker`` script, cut and paste the following line to your terminal to use the wft4galaxy docker image based on ``alpine`` linux:

.. code-block:: bash

  sudo curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/install.sh |  sudo bash /dev/stdin alpine

or the following to use an ``ubuntu`` based image:

.. code-block:: bash

  sudo curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/install.sh |  sudo bash /dev/stdin ubuntu

If your ``PATH`` exports ``/usr/local/bin``, then you would have the ``wft4galaxy-docker`` script immediately available from your terminal.

.. note:: The two versions are equivalent since they have the same set of packages installed. But the ``alpine`` linux version is preferable due to its smaller size (~250 MB), about the half of the equivalent based on ubuntu (~548.3 MB).


Basic Usage
===========
Using ``wft4galaxy-docker`` you can launch your Galaxy workflow tests as you do with the ``wft4galaxy`` script provided by native installation of **wft4galaxy** (see :ref:`getting_started` section).

Thus, you can run all tests definied in a workflow-test-suite configuration file, like ``examples/workflow-testsuite-conf.yml`` (see :ref:`config-file` for more details about the syntax), by simply tiping:

.. code-block:: bash

  wft4galaxy-docker -f examples/workflow-testsuite-conf.yml -o results

... i.e., the same syntax supported by the ``wft4galaxy`` script (see :ref:`getting_start` for more details).


Advanced Usage
==============
The ``wft4galaxy-docker`` script provides several and optional usage modes, as its ``help`` option (i.e., ``wft4galaxy-docker --help``) shows:

.. code-block:: bash

  Usage: wft4galaxy-docker [-m|--mode <MODE>] [-e|--entrypoint <MODE_ENTRYPOINT>] [ENTRYPOINT_OPTIONS] [GLOBAL_OPTIONS] [DOCKER_OPTIONS]
       e.g.: wft4galaxy-docker -m production -e wft4galaxy [wft4galaxy_OPTIONS] (default)
       e.g.: wft4galaxy-docker [wft4galaxy_OPTIONS] (default)

    MODEs:
	  1) production (default)
	  2) develop

    MODE ENTRYPOINTs:
	  * PRODUCTION MODE: bash, wft4galaxy (default)
	  * DEVELOP MODE:    bash (default), ipython, jupyter, wft4galaxy

    GLOBAL OPTIONs:
      -h, --help            show this help message and exit
      --server=SERVER       Galaxy server URL
      --api-key=API_KEY     Galaxy server API KEY

    DOCKER OPTIONs:         every additional option to pass to the Docker Engine
                            to start the wft4galaxy container
      e.g., -v myhost-folder:/container-host-folder

    ENTRYPOINT OPTIONs:
	  *) jupyter options:
		  -p, --port            jupyter port (default: 9876)

	  *) wft4galaxy options:
		  --enable-logger       Enable log messages
		  --debug               Enable debug mode
		  --disable-cleanup     Disable cleanup
		  -o OUTPUT, --output=OUTPUT
		                        absolute path of the output folder
		  -f FILE, --file=FILE  YAML configuration file of workflow tests

The more relevant considerations are:

  1. it supports two different working modes, **production** and **develop**, implemented by different Docker images.;
  2. each supports a different set of entrypoints. In particular, the *develop* mode allows you to run your tests by using either a ``ipython`` interpreter or a ``jupyter notebook`` runnning within the same docker wft4galaxy container;
  3. global options ``--server`` and ``--api-key`` set respectively the BIOBLEND_GALAXY_URL and BIOBLEND_GALAXY_API_KEY on the environment of the instantiated Docker container;
  4. docker options allow the user to customize the container running the wft4galaxy image.



Direct Docker Usage
===================

For a direct Docker usage the following syntax holds:

.. code-block:: bash

  docker run -it --rm [DOCKER_OPTIONS] crs4/wft4galaxy[-dev][:[alpine|ubuntu]] \
                      <ENTRYPOINT> [GLOBAL_OPTIONS] [ENTRYPOINT_OPTIONS]


.. note:: Docker images are ``crs4/wft4galaxy`` for the *production* mode and ``crs4/wft4galaxy-dev`` for the *develop* mode. An optional tag can be used to specific the base OS used for building the image: only ``alpine`` and ``ubuntu`` are supported.

.. note:: You need to explicitly mount the Docker volumes which are required for reading the configuration file of your suite and write results.
