.. _config_file:

######################
Test Definition File
######################

wft4galaxy supports defining tests in both YAML and JSON formats.


As an example, consider the following YAML test definition file:

.. code-block:: YAML

  ## Galaxy server settings
  ###########################################################################################
  # galaxy_url: "http://192.168.64.8:30700" # default is GALAXY_URL
  # galaxy_api_key: "4b86f51252b5f220012b3e259d0877f9" # default is GALAXY_API_KEY
  ###########################################################################################
  enable_logger: False
  output_folder: "results"

  # workflow tests
  workflows:
    # workflow test "change case"
    change_case:
      file: "change_case/workflow.ga"
      inputs:
        "Input Dataset": "change_case/input"
          #file: "change_case/input"
      expected:
        output1:
          file: "change_case/expected_output_1"
          comparator: "filecmp.cmp"
        output2: "change_case/expected_output_2"

    # workflow test "sacurine"
    sacurine:
      file: "sacurine/workflow.ga"
      params:
        3:
          "orthoI": "NA"
          "predI": "1"
          "respC": "gender"
          "testL": "FALSE"
      inputs:
        "DataMatrix": "sacurine/input/dataMatrix.tsv"
        "SampleMetadata": "sacurine/input/sampleMetadata.tsv"
        "VariableMetadata": "sacurine/input/variableMetadata.tsv"
      expected:
        Univariate_variableMetadata: "sacurine/expected/Univariate_variableMetadata.tsv"
        Multivariate_sampleMetadata: "sacurine/expected/Multivariate_sampleMetadata.tsv"
        Multivariate_variableMetadata: "sacurine/expected/Multivariate_variableMetadata.tsv"
        Biosigner_variableMetadata: "sacurine/expected/Biosigner_variableMetadata.tsv"

The definition has two main parts:

1. **global configuration**, where global settings are defined;
2. **workflow configuration**, which contains workflow-specific settings.


Global settings
---------------

* ``galaxy_url`` and ``galaxy_api``: Galaxy instance and credentials to run the workflows.
* ``output_folder``, if test outputs are to be saved.
* ``logging_level``:  one of ``INFO`` and ``DEBUG`` (default is ``INFO``).
* ``base_path``: path with respect to which the relative file paths are specified -- for
  datasets, workflow files, etc. (see note).

Workflow settings
-----------------

* ``base_path``:  overrides global ``base_path``, if specified (see note).
* ``file``:  workflow file definition (.ga file).
* ``inputs``:  input files for the workflow. More details below.
* ``expected``: output files expected from the workflow in the case of correct
  execution.  More details below.


Base path
~~~~~~~~~

The ``base_path`` is used to locate every relative path specified in a workflow
test configuration (i.e., .ga files, input datasets, expected_output datasets).


It can be set at two levels:

1. **global base_path**: specifies the base path for all workflow tests;
2. **test base_path**: specifies the base path for all files defined within the workflow test

.. note:: If you provide a path starting with ``/`` it is considered absolute and the ``base_path`` setting will not affect it.

The only exception to this logic is for the output directory, which is created
relative to the ``base_path`` if the location is specified in the test
definition (see the ``output_folder`` key) or, if the ``-o`` command line option
is used, in the path specified by the user.


Specifying workflow inputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inputs are specified as a dictionary "Galaxy dataset name" -> file.  Here's an
example:


.. code-block:: YAML

      inputs:
        "DataMatrix": "sacurine/input/dataMatrix.tsv"

In the example, the Galaxy workflow has an input dataset with the label
"DataMatrix."  We're specifying that the file ``sacurine/input/dataMatrix.tsv``
should be used for that input.

The relative path is interpreted relative to the `Base path`_.


Specifying workflow outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Outputs are also specified as a dictionary that has the Galaxy output name as the key.
The associated value can be the path to a file, so that ``wft4galaxy`` will
require that the output dataset generated from the workflow exactly matches the
contents of the file.  Here's an example:

.. code-block:: YAML

      expected:
        Univariate_variableMetadata: "sacurine/expected/Univariate_variableMetadata.tsv"


On the other hand, if required, the comparison operation can be customized
files.  In this case, the ``expected`` looks more like this:

.. code-block:: YAML

      expected:
        Univariate_variableMetadata:
          file: "sacurine/expected/Univariate_variableMetadata.bin"
          comparator: "filecmp.cmp"

The name of the output dataset is still the key the key.  In this case, however,
the value is another dictionary that requires the ``file`` key, to specify the
data file, and the ``comparator`` key, to specify the comparator function.

Comparator function
++++++++++++++++++++++

The comparator function is expected to be a function that accepts two paths as
arguments and is in a Python module that can be imported by ``wft4galaxy`` (so
mind your ``PYTHONPATH``!!).  So, for example, ``filecmp.cmp`` roughly
translates to:

.. code-block:: Python

  import filecmp
  return filecmp.cmp(expected_file_path, generated_file_path)
