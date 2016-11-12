.. _docker:

=====================
Dockerized wft4galaxy
=====================

Basic Usage
===========
Using ``wft4galaxy-docker`` you can launch your Galaxy workflow tests just as you would with the ``wft4galaxy`` script provided by native installation of **wft4galaxy** (see :ref:`installation` section).

Thus, you can run all the tests defined in a workflow test suite definition file, like ``examples/workflow-testsuite-conf.yml`` (see :ref:`config_file` for more details about the syntax), by simply typing:

.. code-block:: bash

  wft4galaxy-docker -f examples/workflow-testsuite-conf.yml -o results

That is, the same syntax supported by the ``wft4galaxy`` script (see :ref:`installation` for more details).

Which Galaxy?
++++++++++++++++

You specify which Galaxy instance ``wft4galaxy-docker`` should use by setting these two environment variables::


    GALAXY_URL                   Galaxy URL
    GALAXY_API_KEY               User API key

You can override this behaviour from the command line with these switches:

.. code-block:: bash

      --server=SERVER       Galaxy server URL
      --api-key=API_KEY     Galaxy server API KEY


Advanced Usage
==============

The ``wft4galaxy-docker`` script also provides several advanced usage options.  Run ``wft4galaxy-docker --help`` to see them all:

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



Development mode
+++++++++++++++++++

``wft4galaxy-docker`` provides a `develop` mode with provides additional entry
points.  Specifically, the *develop* mode allows you to run your tests by using either a ``ipython`` interpreter or a ``jupyter notebook`` running within the wft4galaxy docker container.


Customized container instances
++++++++++++++++++++++++++++++++

All unrecognized command line options are automatically passed to the ``docker``
executable.  You can use this feature to customize your container set-up.  For
instance:

.. code-block:: bash

  wft4galaxy-docker -f examples/testsuite.yml -o results -v myhost-folder:/container-host-folder



Direct Docker Usage
===================

For a direct Docker usage the following syntax holds:

.. code-block:: bash

  docker run -it --rm [DOCKER_OPTIONS] crs4/wft4galaxy[-dev][:[alpine|ubuntu]] \
                      <ENTRYPOINT> [GLOBAL_OPTIONS] [ENTRYPOINT_OPTIONS]


.. note:: The Docker images are ``crs4/wft4galaxy`` for the *production* mode and ``crs4/wft4galaxy-dev`` for the *develop* mode. An optional tag can be used to specify the base OS used to build the image: only ``alpine`` and ``ubuntu`` are supported.

.. note:: When using ``docker`` directly you will need to explicitly mount the volumes that are required to read the configuration file of your suite and to write results.


.. toctree::
    :hidden:

    Example <notebooks/6_direct_docker_usage.ipynb>

You can find an example `here <notebooks/6_direct_docker_usage.ipynb>`_.
