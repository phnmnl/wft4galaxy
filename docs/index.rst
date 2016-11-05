.. wft4galaxy documentation index

Welcome to wft4galaxy's documentation!
######################################

:ref:`tutorial/notes.ipynb`


.. toctree::
    :maxdepth: 2

    wft4galaxy API <api>


Base path
=========

The notes above hold for every file specified in a workflow test configuration file (i.e., .ga files, input datasets, expected_output datasets). The only exception deals with the actual output which is put within a folder whose path can be either relative to the ``base path`` or to the current folder.

We consider two path levels:

1. **global base_path**: specifies the base path for all workflow tests;
2. **wofkflow test base_path**: specifies the base path for all files defined within the workflow test

.. note:: If you provide file name starting with ``/`` its path is considered absolute and possible ``base_path`` will be ignored.




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :ref:`tutorial/notes.ipynb`
