#!/usr/bin/env python

from __future__ import print_function
from future.utils import iteritems as _iteritems
from past.builtins import basestring as _basestring

import os as _os
import logging as _logging
from json import dumps as _json_dumps
from uuid import uuid1 as  _uuid1

from yaml import dump as _yaml_dump
from yaml import load as _yaml_load

# wft4galaxy dependencies
import wft4galaxy.common as _common

# set logger
_logger = _common.LoggerManager.get_logger(__name__)

# Enum magic for Python < 3.4
class Enum(object):
    def __init__(self, **enums):
        for name, val in _iteritems(enums):
            self.__dict__[name] = val

    def __setattr__(self, name, v):
        raise StandardError("Setting enum value not allowed")

    def __iter__(self):
        return iter(self.__dict__.keys())

# Define an Enum for supported output types
OutputFormat = Enum(text='text', xunit='xunit')

class FileFormats(object):
    YAML = "YAML"
    JSON = "JSON"

    @staticmethod
    def is_yaml(file_format):
        return isinstance(file_format, _basestring) and file_format.upper() == FileFormats.YAML

    @staticmethod
    def is_json(file_format):
        return isinstance(file_format, _basestring) and file_format.upper() == FileFormats.JSON


class WorkflowTestCase(object):
    """
    A representation of the configuration of a workflow test.

    :type base_path: str
    :param base_path: base path for workflow and dataset files (the current working path is assumed as default)

    :type workflow_filename: str
    :param workflow_filename: the path (relative to ``base_path``) of the file containing
        the workflow definition (i.e., the ``.ga`` file which can be downloaded from a Galaxy server)

    :type name: str
    :param name: a name for the workflow test

    :type inputs: dict
    :param inputs: a dictionary which defines the mapping between a workflow input and a test dataset.

           :Example:

                {"DataMatrix": "dataMatrix.tsv"} where `DataMatrix` is the name of a workflow input
                and `dataMatrix.tsv` is the file containing the dataset to be used as input for the workflow test.

    :type params: dict
    :param params: a dictionary which defines the mapping between steps and the set of parameters which has to be
        used to configure the corresponding tools of each step.


           :Example:

            .. code-block:: python

                params = {
                            3: {
                                "orthoI": "NA"
                                "predI": "1"
                                "respC": "gender"
                                "testL": "FALSE"
                               }
                         }

    :type expected_outputs: dict
    :param expected_outputs: a dictionary to configure the expected output, i.e., the output which has to be compared
        to the actual one produced by a workflow execution. Each output of a workflow step is eligible to be compared
        with an expected output. It is also possible to specify the python function which has to be used
        to perform the actual comparison. Such a function takes two parameters, i.e., ``actual_output_filename`` and
        ``expected_output_filename``, and returns ``True`` whether the comparison between the two files succeeds and
        ``False`` otherwise.


        :Example: Skeleton of a user-defined comparator:

            .. code-block:: python

                    def compare_outputs(actual_output_filename, expected_output_filename):
                        ....
                        return True | False


        :Example: The example below shows an ``expected_outputs`` dictionary that configures
            the expected output datasets for the two actual workflow outputs ``output1`` and ``output2``.
            A user defined 'comparator' is also given to compare the expected to the actual ``output2``.

            .. code-block:: python

                {
                    'output1': 'change_case/expected_output_1',
                    'output2': {
                        'comparator': 'filecmp.cmp',
                        'file': 'change_case_2/expected_output_2'
                    }
                }



    :type output_folder: str
    :param output_folder: path (relative to ``base_path``) of the folder where workflow outputs are written.
        By default, it is the folder ``results/<name>`` within the ``base_path``
        (where ``name`` is the name of the workflow test).

    :type disable_cleanup: bool
    :param disable_cleanup: ``True`` to avoid the clean up of the workflow and history created on the Galaxy server;
        ``False`` (default) otherwise.

    :type disable_assertions: bool
    :param disable_assertions: ``True`` to disable assertions during the execution of the workflow test;
        ``False`` (default) otherwise.

    """
    # Default settings
    DEFAULT_HISTORY_NAME_PREFIX = "WorkflowTestCase"
    DEFAULT_WORKFLOW_NAME_PREFIX = "WorkflowTest"
    DEFAULT_OUTPUT_FOLDER = "results"
    DEFAULT_CONFIG_FILENAME = "workflow-test-suite.yml"
    DEFAULT_WORKFLOW_CONFIG = {
        "name": "workflow_test_case",
        "file": "workflow.ga",
        "output_folder": DEFAULT_OUTPUT_FOLDER,
        "inputs": {
            "Input Dataset": {"name": "Input Dataset", "file": ["input"]}
        },
        "expected": {
            "output1": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output1"},
            "output2": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output2"}
        }
    }

    def __init__(self, name=None, base_path=".", workflow_filename="workflow.ga", inputs=None, params=None,
                 expected_outputs=None, output_folder=None, disable_cleanup=False, disable_assertions=False,
                 enable_logger=False, enable_debug=False):

        # init properties
        self._base_path = None
        self._filename = None
        self._inputs = {}
        self._params = {}
        self._expected_outputs = {}

        self.enable_logger = enable_logger
        self.enable_debug = enable_debug

        # set parameters
        self.name = str(_uuid1()) if not name else name
        self.set_base_path(base_path)
        self.set_filename(workflow_filename)
        if inputs is not None:
            self.set_inputs(inputs)
        if params is not None:
            self.set_params(params)
        if expected_outputs is not None:
            self.set_expected_outputs(expected_outputs)
        self.output_folder = _os.path.join(self.DEFAULT_OUTPUT_FOLDER, self.name) \
            if output_folder is None else output_folder
        self.disable_cleanup = disable_cleanup
        self.disable_assertions = disable_assertions

    def __str__(self):
        return "WorkflowTestConfig: name={0}, file={1}, inputs=[{2}], expected_outputs=[{3}]".format(
            self.name, self.filename, ",".join(list(self.inputs)), ",".join(list(self.expected_outputs)))

    def __repr__(self):
        return self.__str__()

    @property
    def base_path(self):
        """
        The base path of the workflow file definition and the input and output datasets.
        """
        return self._base_path

    def set_base_path(self, base_path):
        """ Set the base path of the workflow file definition and the input and output datasets.

        :type base_path: str
        :param base_path: a path within the local file system
        """
        self._base_path = base_path

    @property
    def filename(self):
        """
        The filename (relative to ``base_paht``) of the workflow definition.
        """
        return self._filename

    def set_filename(self, filename):
        """ Set the filename (relative to ``base_path``) containing the workflow definition.

        :type filename: str
        :param filename: the path (relative to the ``base_path``) to the ``.ga`` file
        """
        self._filename = filename

    @property
    def inputs(self):
        """
        Return the dictionary which defines the mapping between workflow inputs and test datasets.
        """
        return self._inputs

    def set_inputs(self, inputs):
        """
        Update the mapping between workflow inputs and test datasets.

        :param inputs: dict
        :return: a dictionary of mappings (see :class:`WorkflowTestCase`)
        """
        for name, config in _iteritems(inputs):
            self.add_input(name, config["file"], config["type"] if "type" in config else None)

    def add_input(self, name, path, type_=None):
        """
        Add a new input mapping.

        :type name: str
        :param name: the Galaxy label of an input

        :type path: str
        :param path: the path (relative to the ``base_path``) of the file containing an input dataset
        
        :type type_: str
        :param type_: the type of the input dataset  
        """
        if not name:
            raise ValueError("Input name not defined")
        self._inputs[name] = {"name": name, "file": path if isinstance(path, list) else [path], "type": type_}

    def remove_input(self, name):
        """
        Remove an input mapping.

        :type name: str
        :param name: the Galaxy label of an input

        """
        if name in self._inputs:
            del self._inputs[name]

    def get_input(self, name):
        """
        Return the input mapping for the input labeled as ``name``.

        :type name: str
        :param name: the Galaxy label of the input

        :rtype: dict
        :return: input configuration as dict (e.g., {'name': 'Input Dataset', 'file': "input.txt"})
        """
        return self._inputs.get(name)

    @property
    def params(self):
        """
        Return the dictionary containing the configured parameters (see :class:`WorkflowTestCase`)

        :rtype: dict
        :return: a dictionary of configured parameters
        """
        return self._params

    def set_params(self, params):
        """
        Add a new set of parameters.

        :type params: dict
        :param params: dictionary of parameters indexed by step id (see :class:`WorkflowTestCase`)
        """
        for step_id, step_params in _iteritems(params):
            for name, value in _iteritems(step_params):
                self.add_param(step_id, name, value)

    def add_param(self, step_id, name, value):
        """
        Add a new parameter to the step identified by ``step_id``.

        :type step_id: int
        :param step_id: step index

        :type name: str
        :param name: parameter name

        :type value: str
        :param value: parameter value
        """
        if step_id not in self._params:
            self._params[step_id] = {}
        self._params[step_id][name] = value

    def remove_param(self, step_id, name):
        """
        Remove the parameter labeled ``name`` from the step identified by ``step_id``.

        :type step_id: int
        :param step_id: step index

        :type name: str
        :param name: name of the parameter to be removed
        """
        if step_id in self._params:
            del self._params[step_id][name]

    def get_params(self, step_id):
        """
        Return the dictionary of parameters related to the step identified by 'step_id'.

        :type step_id: int
        :param step_id: the step index

        :rtype: dict
        :return: the dictionary of parameters related to the step identified by 'step_id'
        """
        return self._params.get(step_id)

    def get_param(self, step_id, name):
        """
        Return the value of a specific step parameter.

        :type step_id: int
        :param step_id: the index of the step which the parameter is related to

        :type name: str
        :param name: the name of the parameter to be returned

        :return: the value of the requested parameter
        """
        step_params = self._params.get(step_id)
        return step_params.get(name) if step_params else None

    @property
    def expected_outputs(self):
        """
        A dictionary to configure the expected output, i.e., the output which has to be compared
        to the actual one produced by a workflow execution (see :class:`WorkflowTestCase`).
        """
        return self._expected_outputs

    def set_expected_outputs(self, expected_outputs):
        """
        Add a new set of expected outputs (see :class:`WorkflowTestCase`).

        :type expected_outputs: dict
        :param expected_outputs: a dictionary structured as specified in :class:`WorkflowTestCase`
        """
        for name, config in _iteritems(expected_outputs):
            self.add_expected_output(name, config["file"], config.get("comparator"))

    def add_expected_output(self, name, filename, comparator="filecmp.cmp"):
        """
        Add a new expected output to the workflow test configuration.

        :type name: str
        :param name: the Galaxy name of the output which the expected dataset has to be mapped.

        :type filename: str
        :param filename: the path (relative to the ``base_path``) of the file containing the expected output dataset

        :type comparator: str
        :param comparator: a fully qualified name of a `comparator`function (see :class:`WorkflowTestCase`)
        """
        if not name:
            raise ValueError("Input name not defined")
        self._expected_outputs[name] = {"name": name, "file": filename, "comparator": comparator}

    def remove_expected_output(self, name):
        """
        Remove an expected output from the workflow test configuration.

        :type name: str
        :param name: the Galaxy name of the output which the expected output has to be mapped
        """
        if name in self._expected_outputs:
            del self._expected_outputs[name]

    def get_expected_output(self, name):
        """
        Return the configuration of an expected output.

        :type name: str
        :param name: the Galaxy name of the output which the expected output has to be mapped.

        :rtype: dict
        :return: a dictionary containing the configuration of the expected output as specified
            in :class:`WorkflowTestCase`
        """
        return self._expected_outputs.get(name)

    def to_dict(self):
        """
        Return a dictionary representation of the current class instance.

        :rtype: dict
        :return:
        """
        return dict({
            "name": self.name,
            "file": self.filename,
            "inputs": {name: input_["file"][0] for name, input_ in _iteritems(self.inputs)},
            "params": self.params,
            "expected": self.expected_outputs
        })

    def save(self, filename=None, file_format=FileFormats.YAML):
        """
        Serialize this workflow test configuration to a file (YAML or JSON).

        :type filename: str
        :param filename: absolute path of the file

        :type file_format: str
        :param file_format: ``YAML`` or ``JSON``
        """
        if not filename and not self.filename:
            filename = _os.path.splitext(self.DEFAULT_CONFIG_FILENAME)[0] + \
                       "json" if FileFormats.is_json(file_format) else "yml"
        if not filename:
            filename, _ = _os.path.splitext(self.filename)
            filename += "json" if FileFormats.is_json(file_format) else "yml"
        self.dump(filename=filename, worflow_tests_config=self.to_dict(), file_format=file_format)

    @staticmethod
    def load(filename=DEFAULT_CONFIG_FILENAME,
             workflow_test_name=DEFAULT_WORKFLOW_CONFIG["name"], output_folder=None):
        """
        Load the configuration of a workflow test suite or a single workflow test
        from a YAML or JSON configuration file.

        :type filename: str
        :param filename: the path of the file containing the suite definition

        :type workflow_test_name: str
        :param workflow_test_name: the optional name of a workflow test (default is "workflow-test-case")

        :type output_folder: str
        :param output_folder: the path of the output folder  

        :rtype: :class:`WorkflowTestCase`
        :return: the :class:`WorkflowTestCase` instance which matches the name 
                provided by the argument `workflow_test_name_`
        """
        if _os.path.exists(filename):
            file_configuration = _load_configuration(filename)
            base_path = file_configuration.get("base_path", _os.path.dirname(_os.path.abspath(filename)))
            output_folder = output_folder \
                            or file_configuration.get("output_folder") \
                            or WorkflowTestCase.DEFAULT_OUTPUT_FOLDER
            # raise an exception if the workflow test we are searching for
            # cannot be found within the configuration file.
            if workflow_test_name not in file_configuration["workflows"]:
                raise KeyError("WorkflowTest with name '{}' not found".format(workflow_test_name))

            wft_config = file_configuration["workflows"][workflow_test_name]
            wft_base_path = _os.path.join(base_path, wft_config.get("base_path", ""))
            wft_output_folder = _os.path.join(output_folder,
                                              wft_config.get("output_folder", workflow_test_name))
            # add the workflow
            return WorkflowTestCase(name=workflow_test_name,
                                    base_path=wft_base_path, workflow_filename=wft_config["file"],
                                    inputs=wft_config["inputs"], params=wft_config.get("params", {}),
                                    expected_outputs=wft_config["expected"],
                                    output_folder=wft_output_folder,
                                    enable_logger=file_configuration.get("enable_logger", False),
                                    enable_debug=file_configuration.get("enable_debug", False))
        else:
            raise ValueError("Filename '{0}' not found".format(filename))

    @staticmethod
    def dump(filename, worflow_tests_config, file_format=FileFormats.YAML):
        """
        Write the configuration of a workflow test suite to a YAML or JSON file.

        :type filename: str
        :param filename: the absolute path of the YAML or JSON configuration file

        :type worflow_tests_config: dict or list
        :param worflow_tests_config: a dictionary which maps a workflow test name
               to the corresponding configuration (:class:`WorkflowTestCase`)
               or a list of :class:`WorkflowTestCase` instances

        :type file_format: str
        :param file_format: ``YAML`` or ``JSON``
        """
        workflows = {}
        config = worflow_tests_config.copy() if isinstance(worflow_tests_config, dict) else {}
        config["workflows"] = workflows

        if isinstance(worflow_tests_config, dict):
            worflow_tests_config = worflow_tests_config["workflows"].values()
        elif not isinstance(worflow_tests_config, list):
            raise ValueError(
                "'workflow_tests_config' must be a configuration dict "
                "or a list of 'WorkflowTestCase' instances")

        for worlflow in worflow_tests_config:
            workflows[worlflow.name] = worlflow.to_dict()
        with open(filename, "w") as f:
            if FileFormats.is_yaml(file_format):
                _yaml_dump(config, f)
            else:
                f.write(_json_dumps(config, indent=2))
        return config

    def run(self, galaxy_url=None, galaxy_api_key=None, output_folder=None,
            enable_xunit=False, xunit_file=None, verbosity=0,
            enable_logger=None, enable_debug=None, disable_cleanup=None):
        _common.LoggerManager.configure_logging(
            _logging.DEBUG if enable_debug is True else _logging.INFO if enable_logger is True else _logging.ERROR)
        import wft4galaxy.runner as _runner
        return _runner.WorkflowTestsRunner(
            galaxy_url, galaxy_api_key).run(self, verbosity=verbosity,
                                            output_folder=output_folder or self.output_folder,
                                            report_format="xunit" if enable_xunit else None,
                                            report_filename=xunit_file,
                                            enable_logger=enable_logger, enable_debug=enable_debug,
                                            disable_cleanup=disable_cleanup)


class WorkflowTestSuite(object):
    """
    Represent a test suite.
    """

    def __init__(self, galaxy_url=None, galaxy_api_key=None,
                 output_folder=WorkflowTestCase.DEFAULT_OUTPUT_FOLDER,
                 enable_logger=True, enable_debug=False, disable_cleanup=False, disable_assertions=False):
        """
        Create an instance of :class:`WorkflowTestSuite`.

        :type galaxy_url: str
        :param galaxy_url: url of your Galaxy server instance.  If ``none``, the environment variable
            ``GALAXY_URL`` is used. An error is raised when such a variable cannot be found.

        :type galaxy_api_key: str
        :param galaxy_api_key: an API key from your Galaxy server instance.  If ``none``, the environment variable
            ``GALAXY_API_KEY`` is used. An error is raised when such a variable cannot be found.
        """

        self.galaxy_url = galaxy_url
        self.galaxy_api_key = galaxy_api_key
        self.enable_logger = enable_logger
        self.enable_debug = enable_debug
        self.disable_cleanup = disable_cleanup
        self.disable_assertions = disable_assertions
        self.output_folder = output_folder
        # instantiate the dict for worklofws
        self._workflows = {}

    @property
    def workflow_tests(self):
        """
        Return the configuration of workflow tests associated to this test suite.

        :rtype: dict
        :return: a dictionary which maps a `workflow test name` to the :class:`WorkflowTestCase` instance
            representing its configuration
        """
        return self._workflows.copy()

    def add_workflow_test(self, workflow_test_configuration):
        """
        Add a new workflow test to this suite.

        :type workflow_test_configuration: :class:"WorkflowTestCase"
        :param workflow_test_configuration: the :class:`WorkflowTestCase` instance
            representing the workflow test configuration
        """
        self._workflows[workflow_test_configuration.name] = workflow_test_configuration

    def remove_workflow_test(self, workflow_test):
        """
        Remove a workflow test from this suite.

        :type workflow_test: str or :class:"WorkflowTestCase"
        :param workflow_test: the name of the workflow test to be removed
            or the :class:`WorkflowTestCase` instance representing the workflow test configuration
        """
        if isinstance(workflow_test, WorkflowTestCase):
            del self._workflows[workflow_test.name]
        elif isinstance(workflow_test, _basestring):
            del self._workflows[workflow_test]

    def dump(self, filename):
        """
        Write a suite configuration to a file.

        :type filename: str
        :param filename: the absolute path of the file
        """
        # WorkflowTestCase.dump(filename, self._workflow_test_suite_configuration)
        raise Exception("Not implemented yet!")

    @staticmethod
    def load(filename, output_folder=None):
        if _os.path.exists(filename):
            # TODO: catch YAML parsing errors
            file_configuration = _load_configuration(filename)

            base_path = file_configuration.get("base_path", _os.path.dirname(_os.path.abspath(filename)))
            suite = WorkflowTestSuite(
                galaxy_url=file_configuration.get("galaxy_url"),
                galaxy_api_key=file_configuration.get("galaxy_api_key"),
                enable_logger=file_configuration.get("enable_logger", False),
                enable_debug=file_configuration.get("enable_debug", False),
                disable_cleanup=file_configuration.get("disable_cleanup", False),
                disable_assertions=file_configuration.get("disable_assertions", False),
                output_folder=output_folder \
                              or file_configuration.get("output_folder") \
                              or WorkflowTestCase.DEFAULT_OUTPUT_FOLDER
            )
            for wf_name, wf_config in _iteritems(file_configuration.get("workflows")):
                wf_base_path = _os.path.join(base_path, wf_config.get("base_path", ""))
                wf_config["output_folder"] = _os.path.join(suite.output_folder,
                                                           wf_config.get("output_folder", wf_name))
                # add the workflow
                w = WorkflowTestCase(name=wf_name, base_path=wf_base_path, workflow_filename=wf_config["file"],
                                     inputs=wf_config["inputs"], params=wf_config.get("params", {}),
                                     expected_outputs=wf_config["expected"],
                                     output_folder=wf_config["output_folder"])
                suite.add_workflow_test(w)
            return suite
        else:
            raise ValueError("Filename '{0}' not found".format(filename))

    def run(self, galaxy_url=None, galaxy_api_key=None, tests=None, output_folder=None,
            enable_xunit=False, xunit_file=None, verbosity=0,
            enable_logger=None, enable_debug=None, disable_cleanup=None):
        _common.LoggerManager.configure_logging(
            _logging.DEBUG if enable_debug is True else _logging.INFO if enable_logger is True else _logging.ERROR)
        import wft4galaxy.runner as _runner
        return _runner.WorkflowTestsRunner(
            galaxy_url, galaxy_api_key).run(self, filter=tests, verbosity=verbosity,
                                            output_folder=output_folder or self.output_folder,
                                            report_format="xunit" if enable_xunit else None,
                                            report_filename=xunit_file,
                                            enable_logger=enable_logger, enable_debug=enable_debug,
                                            disable_cleanup=disable_cleanup)


class WorkflowTestResult(object):
    """
    Class for representing the result of a workflow test.
    """

    def __init__(self, test_id, workflow, inputs, outputs, output_history, expected_outputs,
                 missing_tools, results, output_file_map,
                 output_folder=WorkflowTestCase.DEFAULT_OUTPUT_FOLDER, errors=None):
        self.test_id = test_id
        self.workflow = workflow
        self.inputs = inputs
        self.outputs = outputs
        self.errors = [] if errors is None else errors
        self.output_history = output_history
        self.expected_outputs = expected_outputs
        self.output_folder = output_folder
        self.missing_tools = missing_tools
        self.output_file_map = output_file_map
        self.results = results

        self.failed_outputs = {out[0]: out[1]
                               for out in _iteritems(self.results)
                               if not out[1]}

    def __str__(self):
        return "Test {0}: workflow {1}, intputs=[{2}], outputs=[{3}]" \
            .format(self.test_id, self.workflow.name,
                    ",".join([i for i in self.inputs]),
                    ", ".join(["{0}: {1}".format(x[0], "OK" if x[1] else "ERROR")
                               for x in _iteritems(self.results)]))

    def __repr__(self):
        return self.__str__()

    def failed(self):
        """
        Assert whether the test is failed.

        :rtype: bool
        :return: ``True`` if the test is failed; ``False`` otherwise.
        """
        return len(self.failed_outputs) > 0 or len(self.errors) > 0

    def passed(self):
        """
        Assert whether the test is passed.

        :rtype: bool
        :return: ``True`` if the test is passed; ``False`` otherwise.
        """
        return not self.failed()

    def check_output(self, output):
        """
        Assert whether the actual `output` is equal to the expected accordingly
        to its associated `comparator` function.

        :type output: str or dict
        :param output: output name

        :rtype: bool
        :return: ``True`` if the test is passed; ``False`` otherwise.
        """
        return self.results[output if isinstance(output, _basestring) else output.name]

    def check_outputs(self):
        """
        Return a map of pairs <OUTPUT_NAME>:<RESULT>, where <RESULT> is ``True``
        if the actual `OUTPUT_NAME` is equal to the expected accordingly
        to its associated `comparator` function.

        :rtype: dict
        :return: map of output results
        """
        return self.results


class WorkflowTestReportGenerator(object):
    def generate_report(self, stream, report_format="plaintext"):
        raise NotImplementedError()


class WorkflowTestSuiteResult(WorkflowTestReportGenerator, WorkflowTestResult):
    def __init__(self, test_case_results):
        self.test_case_results = test_case_results


class WorkflowTestCaseResult(WorkflowTestReportGenerator, WorkflowTestResult):
    pass


def _load_configuration(config_filename):
    with open(config_filename) as config_file:
        workflows_conf = None
        try:
            workflows_conf = _yaml_load(config_file)
        except ValueError as e:
            _logger.error("Configuration file '%s' is not a valid YAML or JSON file", config_filename)
            raise ValueError("Not valid format for the configuration file '%s'.", config_filename)
    # update inputs/expected fields
    for wf_name, wf in _iteritems(workflows_conf["workflows"]):
        wf["inputs"] = _parse_dict(wf["inputs"])
        wf["expected"] = _parse_dict(wf["expected"])
    return workflows_conf


def _parse_dict(elements):
    results = {}
    for name, value in _iteritems(elements):
        result = value
        if isinstance(value, _basestring):
            result = {"name": name, "file": value}
        elif isinstance(value, dict):
            result["name"] = name
        else:
            raise ValueError("Configuration error: %r", elements)
        results[name] = result
    return results
