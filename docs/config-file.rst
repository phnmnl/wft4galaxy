.. _config_file:

######################
Test Definition File
######################

wft4galaxy support both YAML and JSON formats.


As a reference, consider the following YAML configuration file:

.. code-block:: YAML

  ## Galaxy server settings
  ###########################################################################################
  # galaxy_url: "http://192.168.64.8:30700" # default is BIOBLEND_GALAXY_URL
  # galaxy_api_key: "4b86f51252b5f220012b3e259d0877f9" # default is BIOBLEND_GALAXY_API_KEY
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
        output1: "change_case/expected_output_1"
          #file: "change_case/expected_output_1"
          #comparator: "filecmp.cmp"
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

The wft4galaxy configuration file mainly consists of two parts:

1. **global configuration**, where global settings are defined;
2. **workflow configuration**, which contains workflow specific settings.

Global settings
---------------

* galaxy configurations
* output_folder
* info/debug messages
* base path

Workflow settings
-----------------

* base path (points to global base path); see notes
* workflow file definition (.ga file)
* inputs
* expected_outputs (file + comparator function)



Base path
~~~~~~~~~

The notes above hold for every file specified in a workflow test configuration file (i.e., .ga files, input datasets, expected_output datasets). The only exception deals with the actual output which is put within a folder whose path can be either relative to the ``base path`` or to the current folder.

We consider two path levels:

1. **global base_path**: specifies the base path for all workflow tests;
2. **wofkflow test base_path**: specifies the base path for all files defined within the workflow test

.. note:: If you provide file name starting with ``/`` its path is considered absolute and possible ``base_path`` will be ignored.
