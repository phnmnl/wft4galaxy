.. _installation:

============
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

.. warning:: If are using a linux base system (like *Ubuntu*), probably you need to install \
             the ``python-lxml`` and ``libyaml-dev`` packages as a further requirement.

.. note:: If want to use wft4galaxy with Docker, you can skip the two steps above: see :ref:`docker` for more details.


As a final step, you need to get an **API KEY** from your Galaxy instance, which can be done
from the *'User'* menu of the web Galaxy interface. This API KEY, together with the URL of your Galaxy instance
(i.e., ``http://192.168.64.2:30700``), must be provided to wft4galaxy in order for it to connect
to and communicate with that server. This can be done either passing them as parameters to the command line script
(see CLI options :ref:`notebooks/1_run_suite_from_cli.ipynb`) and to the the main API endpoints
(see :ref:`programmatic_usage`) or setting them as environment variables; i.e.:

.. code-block:: bash

  export GALAXY_URL="<YOUR_GALAXY_SERVER_URL>"
  export GALAXY_API_KEY="<YOUR_GALAXY_API_KEY>"


Docker-based Installation
++++++++++++++++++++++++++++

**wft4galaxy** can also run within a Docker container, without installation.

To simplify the usage of the Docker images by command line, we provide a simple script mainly intended
to allow users to interact with the dockerized version of the tool as if it was "native",
i.e., like a locally installed ``wft4galaxy``. This script is called ``wft4galaxy-docker``.

Installation
------------

To install ``wft4galaxy-docker`` so that it is available system-wide, you can use
the following command which will download and install the script to
``/usr/local/bin``:

.. code-block:: bash

  curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/master/utils/docker/install.sh | bash

If your ``PATH`` includes ``/usr/local/bin`` you will have the ``wft4galaxy-docker`` script
immediately available from your terminal. Alternatively, you can install the ``wft4galaxy-docker`` script
in any other folder of your system by simply appending the string ``/dev/stdin <TARGET_FOLDER>``
to the line above, replacing ``TARGET_FOLDER`` with the folder you want to use for installation.
For example, if you want to install the script to your current directory, cut and paste the following line to your terminal:

.. code-block:: bash

  curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/master/utils/docker/install.sh | bash /dev/stdin .

Then, type ``./wft4galaxy-docker`` to launch from your current path.
