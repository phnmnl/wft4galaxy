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


As a final step, you need to get an **API KEY** from your Galaxy instance, which can be done from the *'User'* menu of the web Galaxy interface. Such API KEY, together with the URL of your Galaxy instance (i.e., ``http://192.168.64.2:30700``), must be provided to wft4galaxy in order for it to connect and communicate to that server. This can be done either passing them as parameters to the command line script (see CLI options ?????) and to the the main API endpoints (see :ref:`programmatic_usage`) or setting them as environment variables; i.e.:

.. code-block:: bash

  export BIOBLEND_GALAXY_URL="<YOUR_GALAXY_SERVER_URL>"
  export BIOBLEND_GALAXY_API_KEY="<YOUR_GALAXY_API_KEY>"
