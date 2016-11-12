.. _installation:

Installation
============

To install **wft4galaxy** as native Python library, you have to:

1. clone the corresponding github repository:

.. code-block:: bash

  git clone https://github.com/phnmnl/wft4galaxy

2. install the package from source code using the usual Python ``setup.py``:

.. code-block:: bash

  python setup.py install [--user]

.. note:: Use the option ``--user`` to install the module only for the current user.

.. warning:: If are using a linux base system (like *Ubuntu*), probably you need to install the ``python-lxml`` and ``libyaml-dev`` packages as a further requirement.

.. note:: If want to use wft4galaxy with Docker, you can skip the two steps above: see :ref:`docker` for more details.


As a final step, you need to get an **API KEY** from your Galaxy instance, which can be done from the *'User'* menu of the web Galaxy interface. This API KEY, together with the URL of your Galaxy instance (i.e., ``http://192.168.64.2:30700``), must be provided to wft4galaxy in order for it to connect to and communicate with that server. This can be done either passing them as parameters to the command line script (see CLI options :ref:`notebooks/1_run_suite_from_cli.ipynb`) and to the the main API endpoints (see :ref:`programmatic_usage`) or setting them as environment variables; i.e.:

.. code-block:: bash

  export GALAXY_URL="<YOUR_GALAXY_SERVER_URL>"
  export GALAXY_API_KEY="<YOUR_GALAXY_API_KEY>"


Docker-based Installation
++++++++++++++++++++++++++++

**wft4galaxy** can also run within a Docker container, without installation.

To simplify the usage of the Docker images by command line, we provide a simple script mainly intended to allow users to interact with the dockerized version of the tool as if it was "native", i.e., like a locally installed ``wft4galaxy``. This script is called ``wft4galaxy-docker``.

Installation
------------

To install ``wft4galaxy-docker`` so that it is available system-wide, you can use
one of the following commands to download and install the script to
``/usr/local/bin``.

Cut and paste the following line to your terminal to use the wft4galaxy docker image based on ``alpine`` linux:

.. code-block:: bash

  curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/install.sh |  sudo bash /dev/stdin alpine

Alternatively, the following command will give you an ``ubuntu``-based image:

.. code-block:: bash

  curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/install.sh |  sudo bash /dev/stdin ubuntu

If your ``PATH`` includes ``/usr/local/bin`` you will have the ``wft4galaxy-docker`` script immediately available from your terminal.

.. note:: The two versions are equivalent since they have the same set of packages installed. But the ``alpine`` linux version is preferable due to its smaller size (~250 MB), about the half of the equivalent based on ubuntu (~548.3 MB).

