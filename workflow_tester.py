#!/usr/bin/env python

import os as _os

import logging as _logging
import unittest as _unittest
import optparse as _optparse

from uuid import uuid1 as  _uuid1
from sys import exc_info as _exc_info
from difflib import unified_diff as _unified_diff
from yaml import load as _yaml_load, dump as _yaml_dump
from json import load as _json_load, dumps as _json_dumps

from bioblend.galaxy.objects import GalaxyInstance as _GalaxyInstance
from bioblend.galaxy.workflows import WorkflowClient as _WorkflowClient
from bioblend.galaxy.histories import HistoryClient as _HistoryClient

# Galaxy ENV variable names
ENV_KEY_GALAXY_URL = "BIOBLEND_GALAXY_URL"
ENV_KEY_GALAXY_API_KEY = "BIOBLEND_GALAXY_API_KEY"

# configure module logger
_logger = _logging.getLogger("WorkflowTest")
_logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')


class WorkflowTestConfiguration:
    """
    Utility class for programmatically handle a workflow test configuration.
    """
    # Default settings
    DEFAULT_HISTORY_NAME_PREFIX = "_WorkflowTestHistory_"
    DEFAULT_WORKFLOW_NAME_PREFIX = "_WorkflowTest_"
    DEFAULT_OUTPUT_FOLDER = "results"
    DEFAULT_CONFIG_FILENAME = "workflows.yml"
    DEFAULT_WORKFLOW_CONFIG = {
        "file": "workflow.ga",
        "inputs": {
            "Input Dataset": {"name": "Input Dataset", "file": ["input"]}
        },
        "expected": {
            "output1": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output1"},
            "output2": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output2"}
        }
    }

    def __init__(self, name=None, base_path=".", filename="workflow.ga", inputs={}, expected_outputs={},
                 output_folder=None, disable_cleanup=True, disable_assertions=True):
        """
        Create a new class instance and initialize its initial properties.

        :type base_path: str
        :param base_path: base path for workflow and datasets files; the current path is assumed as default

        :type filename: str
        :param filename: the path (relative to the basepath) of the file containing the workflow definition

        :type name: str
        :param name: the name of the workflow test

        :type inputs: dict
        :param inputs: a map <INPUT_NAME>:<INPUT_DATASET_INFO> (e.g., {"input_name" : {"file": ...}}

        :type expected_outputs: dict
        :param expected_outputs: maps actual to expected outputs.
               Each output requires a dict containing the path of the expected output filename
               and the fully qualified name of a function which will be used to compare the expected
               to the actual output. Such a function takes ``actual_output_filename`` and ``expected_output_filename``
               as parameters and returns ``True`` if the comparison succeeds, ``False``otherwise.

               Example of expected_outputs:

                    :Example:

                                {'output1': {'comparator': 'filecmp.cmp',
                                             'file': 'change_case_1/expected_output_1',
                                             'name': 'output1'}}

               Comparator function signature:

                    :Example:

                        def compare_outputs(actual_output_filename, expected_output_filename):
                            ....
                            return True | False

        :type output_folder: str
        :param output_folder: absolute path of the folder where output is written

        :type disable_cleanup: bool
        :param disable_cleanup: ``True`` to skip cleanup (Galaxy workflow, history, datasets)
                        after the workflow test execution; ``False`` (default) otherwise.

        :type disable_assertions: bool
        :param disable_assertions: ``True`` to disable assertions during the workflow test execution;
                           ``False`` (default) otherwise.
        """

        # init properties
        self._base_path = None
        self._filename = None
        self._inputs = {}
        self._expected_outputs = {}

        # set parameters
        self.name = _uuid1() if not name else name
        self.set_base_path(base_path)
        self.set_filename(filename)
        self.set_inputs(inputs)
        self.set_expected_outputs(expected_outputs)
        self.output_folder = _os.path.join(self.DEFAULT_OUTPUT_FOLDER, self.name) \
            if output_folder is None else output_folder
        self.disable_cleanup = disable_cleanup
        self.disable_assertions = disable_assertions

    def __str__(self):
        return "WorkflowTestConfig: name={0}, file={1}, inputs=[{2}], expected_outputs=[{3}]".format(
            self.name, self.filename, ",".join(self.inputs.keys()), ",".join(self.expected_outputs.keys()))

    def __repr__(self):
        return self.__str__()

    @property
    def base_path(self):
        return self._base_path

    def set_base_path(self, base_path):
        """ Set the base path to ``base_path``.

        :type name: str
        :param base_path: base path for workflow and datasets files; the current path is assumed as default
        """
        self._base_path = base_path

    @property
    def filename(self):
        return self._filename

    def set_filename(self, filename):
        """ Set the filename of the workflow definition.

        :type filename: str
        :param filename: the path (relative to the basepath) of the file containing the workflow definition
        """
        self._filename = filename

    @property
    def inputs(self):
        return self._inputs

    def set_inputs(self, inputs):
        """
        Add a set of inputs.

        :param inputs: dict
        :return: a map <INPUT_NAME>:<INPUT_DATASET_INFO> (e.g., {"input_name" : {"file": ...}}
        """
        for name, config in inputs.items():
            self.add_input(name, config["file"])

    def add_input(self, name, file):
        """
        Add a new input.

        :type name: str
        :param name: the Galaxy label of the input

        :type file: str
        :param file: the path (relative to the basepath) of the file containing the input dataset
        """
        if not name:
            raise ValueError("Input name not defined")
        self._inputs[name] = {"name": name, "file": file if isinstance(file, list) else [file]}

    def remove_input(self, name):
        """
        Remove an input.

        :type name: str
        :param name: the Galaxy label of the input

        """
        if name in self._inputs:
            del self._inputs[name]

    def get_input(self, name):
        """
        Return the input configuration.

        :type name: str
        :param name: the Galaxy label of the input

        :rtype: dict
        :return: input configuration as dict (e.g., {'name': 'Input Dataset', 'file': "input.txt"})
        """
        return self._inputs.get(name, None)

    @property
    def expected_outputs(self):
        return self._expected_outputs

    def set_expected_outputs(self, expected_outputs):
        """
        Add a set of expected outputs which are intended to map actual to expected outputs.

        :type expected_outputs: dict
        :param expected_outputs: map actual to expected outputs.
               Each output requires a dict containing the path of the expected output filename
               and the fully qualified name of a function which will be used to compare the expected
               to the actual output. Such a function takes ``actual_output_filename`` and ``expected_output_filename``
               as parameters and returns ``True`` if the comparison succeeds, ``False``otherwise.

               .. example: {'output1': {'comparator': 'filecmp.cmp',
                                        'file': 'change_case_1/expected_output_1',
                                        'name': 'output1'}}
        """
        for name, config in expected_outputs.items():
            self.add_expected_output(name, config["file"], config.get("comparator", None))

    def add_expected_output(self, name, filename, comparator="filecmp.cmp"):
        """
        Add a new expected output to the workflow test configuration.

        :type name: str
        :param name: the Galaxy name of the output which the expected output has to be mapped.

        :type filename: str
        :param filename: the path (relative to the basepath) of the file containing the expected_output dataset

        :type comparator: str
        :param comparator: a fully qualified name of a `comparator`function

               :Example:

                        def compare_outputs(actual_output_filename, expected_output_filename):
                            ....
                            return True | False

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
        :return
        """
        return self._expected_outputs.get(name, None)

    def to_json(self):
        """
        Return a dict representation of the current class instance.

        :rtype: dict
        :return:
        """
        return dict({
            "name": self.name,
            "file": self.filename,
            "inputs": {name: input["file"][0] for name, input in self.inputs.items()},
            "expected": self.expected_outputs
        })

    @staticmethod
    def load(filename=DEFAULT_CONFIG_FILENAME, workflow_test_name=None):
        """
        Load the configuration of a workflow test suite or a single workflow test from a YAML file.

        :type filename: str
        :param filename: the path of the file containing the suite definition

        :type workflow_test_name: str
        :param workflow_test_name: the name of a workflow test name

        :rtype: dict
        :return:
        """

        config = {}
        if _os.path.exists(filename):
            base_path = _os.path.dirname(_os.path.abspath(filename))
            workflows_conf = _load_configuration(filename)
            config["galaxy_url"] = workflows_conf.get("galaxy_url", None)
            config["galaxy_api_key"] = workflows_conf.get("galaxy_api_key", None)
            config["enable_logger"] = workflows_conf.get("enable_logger", False)
            config["output_folder"] = workflows_conf.get("output_folder",
                                                         WorkflowTestConfiguration.DEFAULT_OUTPUT_FOLDER)
            config["workflows"] = {}
            for wf_name, wf_config in workflows_conf.get("workflows").items():
                wf_config["output_folder"] = _os.path.join(config["output_folder"],
                                                           wf_config.get("output_folder", wf_name))
                # add the workflow
                w = WorkflowTestConfiguration(name=wf_name, base_path=base_path, filename=wf_config["file"],
                                              inputs=wf_config["inputs"], expected_outputs=wf_config["expected"],
                                              output_folder=wf_config["output_folder"])
                config["workflows"][wf_name] = w
                # returns the current workflow test config
                # if its name matches the 'workflow_test_name' param
                if workflow_test_name and wf_name == workflow_test_name:
                    return w
            # raise an exception if the workflow test we are searching for
            # cannot be found within the configuration file.
            if workflow_test_name:
                raise KeyError("WorkflowTest with name '%s' not found" % workflow_test_name)
        else:
            config["workflows"] = {"unknown": WorkflowTestConfiguration.DEFAULT_WORKFLOW_CONFIG.copy()}
        config["output_folder"] = WorkflowTestConfiguration.DEFAULT_OUTPUT_FOLDER
        return config

    @staticmethod
    def dump(filename, worflow_test_list):
        """
        Write the configuration of a workflow test suite to a YAML file.

        :type filename: str
        :param filename: the absolute path of the YAML file

        :type worflow_test_list: dict
        :param worflow_test_list: a dictionary which maps a workflow test name
               to the corresponding configuration (:class:`WorkflowTestConfiguration`)
        """

        workflows = {}
        config = {"workflows": workflows}
        worflow_test_list = worflow_test_list.values() if isinstance(worflow_test_list, dict) else worflow_test_list

        for worlflow in worflow_test_list:
            workflows[worlflow.name] = worlflow.to_json()
        with open(filename, "w") as f:
            _yaml_dump(config, f)
        return config


class WorkflowLoader:
    """
    Utility class responsible for loading/unloading workflows to a Galaxy server.
    """

    _instance = None

    @staticmethod
    def get_instance():
        """
        Return the singleton instance of this class.

        :rtype: :class:`WorkflowLoader`
        :return: a workflow loader instance
        """
        if not WorkflowLoader._instance:
            WorkflowLoader._instance = WorkflowLoader()
        return WorkflowLoader._instance

    def __init__(self, galaxy_instance=None):
        """
        Create a new instance of this class
        It requires a ``galaxy_instance`` (:class:`bioblend.GalaxyInstance`) which can be provided
        as a constructor parameter (if it has already been instantiated) or configured (and instantiated)
        by means of the method ``initialize``.

        :type galaxy_instance: :class:`bioblend.GalaxyInstance`
        :param galaxy_instance: a galaxy instance object
        """
        self._galaxy_instance = galaxy_instance
        self._galaxy_workflow_client = None
        self._workflows = {}
        # if galaxy_instance exists, complete initialization
        if galaxy_instance:
            self.initialize()

    def initialize(self, galaxy_url=None, galaxy_api_key=None):
        """
        Initialize the required ``galaxy_instance``.

        :type galaxy_url: str
        :param galaxy_url: the URL of the Galaxy server

        :type galaxy_api_key: str
        :param galaxy_api_key: a registered Galaxy API KEY
        """
        if not self._galaxy_instance:
            # initialize the galaxy instance
            self._galaxy_instance = _get_galaxy_instance(galaxy_url, galaxy_api_key)
        # initialize the workflow client
        self._galaxy_workflow_client = _WorkflowClient(self._galaxy_instance.gi)

    def load_workflow(self, workflow_test_config, workflow_name=None):
        """
        Load a workflow defined in a :class:`WorkflowTestConfig` instance to the configured Galaxy server.

        :type workflow_test_config: :class:`WorkflowTestConfig`
        :param workflow_test_config: the configuration of the workflow test

        :type workflow_name: str
        :param workflow_name: an optional name which overrides the workflow name
        """
        workflow_filename = workflow_test_config.filename \
            if not workflow_test_config.base_path \
            else _os.path.join(workflow_test_config.base_path, workflow_test_config.filename)
        return self.load_workflow_by_filename(workflow_filename, workflow_name)

    def load_workflow_by_filename(self, workflow_filename, workflow_name=None):
        """
        Load a workflow defined within the `workflow_filename` file to the configured Galaxy server.

        :type workflow_filename: str
        :param workflow_filename: the path of workflow definition file

        :type workflow_name: str
        :param workflow_name: an optional name which overrides the workflow name
        :return:
        """
        with open(workflow_filename) as f:
            wf_json = _json_load(f)
        # TODO: register workflow by ID (equal to UUID?)
        if not wf_json["name"] in self._workflows:
            wf_name = wf_json["name"]
            wf_json["name"] = WorkflowTestConfiguration.DEFAULT_WORKFLOW_NAME_PREFIX \
                              + (workflow_name if workflow_name else wf_name)
            wf_info = self._galaxy_workflow_client.import_workflow_json(wf_json)
            workflow = self._galaxy_instance.workflows.get(wf_info["id"])
            self._workflows[wf_name] = workflow
        else:
            workflow = self._workflows[wf_json["name"]]
        return workflow

    def unload_workflow(self, workflow_id):
        """
        Unload a workflow from the configured Galaxy server.

        :type workflow_id: str
        :param workflow_id: the ID of the workflow to unload.
        """
        self._galaxy_workflow_client.delete_workflow(workflow_id)
        # TODO: remove workflow from the list

    def unload_workflows(self):
        for wf_name, wf in self._workflows.items():
            self.unload_workflow(wf[id])


class WorkflowTestSuite:
    """
    Define a test suite.
    """

    _DEFAULT_SUITE_CONFIGURATION = {
        "enable_logger": True,
        "enable_debug": False,
        "disable_cleanup": False,
        "disable_assertions": False,
        "workflows": {}
    }

    def __init__(self, galaxy_url=None, galaxy_api_key=None):
        """
        Create an instance of :class:`WorkflowTestSuite`.

        :type galaxy_url: str
        :param galaxy_url: the URL of a Galaxy server (e.g., http://192.168.64.6:30700)

        :type galaxy_api_key: str
        :param galaxy_api_key: the API KEY registered in the Galaxy server.
        """
        self._workflows = {}
        self._workflow_runners = []
        self._workflow_test_results = []
        self._galaxy_instance = None
        self._galaxy_workflow_client = None
        # initialize the galaxy instance
        self._galaxy_instance = _get_galaxy_instance(galaxy_url, galaxy_api_key)
        # initialize the workflow loader
        self._workflow_loader = WorkflowLoader(self._galaxy_instance)
        # default suite configuration
        self._workflow_test_suite_configuration = WorkflowTestSuite._DEFAULT_SUITE_CONFIGURATION.copy()

    @property
    def galaxy_instance(self):
        return self._galaxy_instance

    @property
    def workflow_loader(self):
        return self._workflow_loader

    @property
    def configuration(self):
        return self._workflow_test_suite_configuration

    # def get_workflows(self):
    #     """
    #
    #     :rtype: list
    #     :return: list of :class:`bioblend:Workflow
    #     """
    #     return self.galaxy_instance.workflows.list()

    def get_workflow_test_results(self, workflow_id=None):
        """
        Return the list of :class:`WorkflowTestResult` instances resulting by the executed workflow tests.
        Such a list can be filtered by workflow, specified as `workflow_id`.

        :type workflow_id: str
        :param workflow_id: the optional ID of a workflow

        :rtype: list
        :return: a list of :class:`WorkflowTestResult`
        """
        return list([w for w in self._workflow_test_results if w.id == workflow_id] if workflow_id
                    else self._workflow_test_results)

    @property
    def workflow_tests(self):
        """
        Return the configurations of the workflows associated to this test suite.

        :rtype: dict
        :return: a map <WORKFLOW_TEST_NAME> : <WORKFLOW_TEST_CONFIGURATION>
        """
        return self._workflow_test_suite_configuration["workflows"].copy()

    def add_workflow_test(self, workflow_test_configuration):
        """
        Add a new workflow test to this suite.

        :type workflow_test_configuration: :class:"WorkflowTestConfiguration"
        :param workflow_test_configuration: a workflow test configuration
        """
        self._workflow_test_suite_configuration["workflows"][
            workflow_test_configuration.name] = workflow_test_configuration

    def remove_workflow_test(self, workflow_test):
        """
        Remove a workflow test from this suite.

        :type workflow_test: str or :class:"WorkflowTestConfiguration"
        :param workflow_test: the name of the workflow test to remove or its configuration
        """
        if isinstance(workflow_test, WorkflowTestConfiguration):
            del self._workflow_test_suite_configuration[workflow_test.name]
        elif isinstance(workflow_test, str):
            del self._workflow_test_suite_configuration[workflow_test]

    def _add_test_result(self, test_result):
        """
        Private method to publish a test result.

        :type test_result: :class:'WorkflowTestResult'
        :param test_result: an instance of :class:'WorkflowTestResult'
        """
        self._workflow_test_results.append(test_result)

    def _create_test_runner(self, workflow_test_config):
        """
        Private method which creates a test runner associated to this suite.

        :type workflow_test_config: :class:'WorkflowTestConfig'
        :param workflow_test_config:

        :rtype: :class:'WorkflowTestRunner'
        :return: the created :class:'WorkflowTestResult' instance
        """
        runner = WorkflowTestRunner(self.galaxy_instance, self.workflow_loader, workflow_test_config, self)
        self._workflow_runners.append(runner)
        return runner

    def _suite_setup(self, config, enable_logger=None,
                     enable_debug=None, disable_cleanup=None, disable_assertions=None):
        config["enable_logger"] = enable_logger if not enable_logger is None else config.get("enable_logger", True)
        config["enable_debug"] = enable_debug if not enable_debug is None else config.get("enable_debug", False)
        config["disable_cleanup"] = disable_cleanup \
            if not disable_cleanup is None else config.get("disable_cleanup", False)
        config["disable_assertions"] = disable_assertions \
            if not disable_assertions is None else config.get("disable_assertions", False)
        # update logger level
        if config.get("enable_logger", True):
            config["logger_level"] = _logging.DEBUG if config.get("enable_debug", False) else _logging.INFO
            _logger.setLevel(config["logger_level"])

    def run_tests(self, workflow_tests_config=None, enable_logger=None,
                  enable_debug=None, disable_cleanup=None, disable_assertions=None):
        """
        Execute tests associated to this suite and return the corresponding results.

        :type workflow_tests_config: dict
        :param workflow_tests_config: a suite configuration as produced
               by the `WorkflowTestConfiguration.load(...)` method

        :rtype: list
        :return: the list of :class:'WorkflowTestResult' instances
        """
        results = []
        suite_config = workflow_tests_config or self._workflow_test_suite_configuration
        self._suite_setup(suite_config, enable_logger, enable_debug, disable_cleanup, disable_assertions)
        for test_config in suite_config["workflows"].values():
            runner = self._create_test_runner(test_config)
            result = runner.run_test()
            results.append(result)
        # cleanup
        if not suite_config["disable_cleanup"]:
            self.cleanup()
        return results

    def run_test_suite(self, workflow_tests_config=None, enable_logger=None,
                       enable_debug=None, disable_cleanup=None, disable_assertions=None):
        """
        Execute tests associated to this suite using the unittest framework.

        :type workflow_tests_config: dict
        :param workflow_tests_config: a suite configuration as produced
               by the `WorkflowTestConfiguration.load(...)` method
        """
        suite = _unittest.TestSuite()
        suite_config = workflow_tests_config or self._workflow_test_suite_configuration
        self._suite_setup(suite_config, enable_logger, enable_debug, disable_cleanup, disable_assertions)
        for test_config in suite_config["workflows"].values():
            runner = self._create_test_runner(test_config)
            suite.addTest(runner)
        _RUNNER = _unittest.TextTestRunner(verbosity=2)
        _RUNNER.run((suite))
        # cleanup
        if not suite_config["disable_cleanup"]:
            self.cleanup()

    def cleanup(self):
        """
        Perform a cleanup unloading workflows and deleting temporary histories.
        """
        _logger.debug("Cleaning save histories ...")
        hslist = self.galaxy_instance.histories.list()
        for history in [h for h in hslist if WorkflowTestConfiguration.DEFAULT_HISTORY_NAME_PREFIX in h.name]:
            self.galaxy_instance.histories.delete(history.id)
        _logger.debug("Cleaning workflow library ...")
        wflist = self.galaxy_instance.workflows.list()
        workflows = [w for w in wflist if WorkflowTestConfiguration.DEFAULT_WORKFLOW_NAME_PREFIX in w.name]
        for wf in workflows:
            self._workflow_loader.unload_workflow(wf.id)

    def load(self, filename=None):
        """
        Load a test suite configuration and set it as default suite to run.

        :type filename: str
        :param filename: the path of suite configuration file
        """
        self._workflow_test_suite_configuration = WorkflowTestSuite._DEFAULT_SUITE_CONFIGURATION.copy()
        self._workflow_test_suite_configuration.update(
            WorkflowTestConfiguration.load(filename or WorkflowTestConfiguration.DEFAULT_CONFIG_FILENAME))

    def dump(self, filename):
        WorkflowTestConfiguration.dump(filename or WorkflowTestConfiguration.DEFAULT_CONFIG_FILENAME,
                                       self._workflow_test_suite_configuration)


class WorkflowTestRunner(_unittest.TestCase):
    """
    Class responsible for launching tests.
    """

    def __init__(self, galaxy_instance, workflow_loader, workflow_test_config, test_suite=None):
        self._galaxy_instance = galaxy_instance
        self._workflow_loader = workflow_loader
        self._workflow_test_config = workflow_test_config
        self._test_suite = test_suite
        self._galaxy_history_client = _HistoryClient(galaxy_instance.gi)
        self._disable_cleanup = workflow_test_config.disable_cleanup
        self._disable_assertions = workflow_test_config.disable_assertions
        self._output_folder = workflow_test_config.output_folder
        self._base_path = workflow_test_config.base_path
        self._test_cases = {}
        self._test_uuid = None
        self._galaxy_workflow = None

        setattr(self, "test_" + workflow_test_config.name, self.run_test)
        super(WorkflowTestRunner, self).__init__("test_" + workflow_test_config.name)

    @staticmethod
    def new_instance(workflow_test_config, galaxy_url=None, galaxy_api_key=None):
        """
        Factory method to create and initialize an instance of :class:`WorkflowTestRunner`.

        :type workflow_test_config: :class:`WorkflowTestConfiguration`
        :param workflow_test_config: the configuration of a workflow test

        :type galaxy_url: str
        :param galaxy_url: the URL of the Galaxy server

        :type galaxy_api_key: str
        :param galaxy_api_key: a registered Galaxy API KEY

        :rtype: :class:`WorkflowTestRunner`
        :return: a :class:`WorkflowTestRunner` instance
        """
        # initialize the galaxy instance
        galaxy_instance = _get_galaxy_instance(galaxy_url, galaxy_api_key)
        workflow_loader = WorkflowLoader(galaxy_instance)
        # return the runner instance
        return WorkflowTestRunner(galaxy_instance, workflow_loader, workflow_test_config)

    @property
    def workflow_test_config(self):
        return self._workflow_test_config

    @property
    def worflow_test_name(self):
        return self._workflow_test_config.name

    def __str__(self):
        return "Workflow Test: '{0}'".format(self._workflow_test_config.name)

    def to_string(self):
        return "Workflow Test '{0}': testId={1}, workflow='{2}', input=[{3}], output=[{4}]" \
            .format(self._workflow_test_config.name,
                    self._get_test_uuid(),
                    self._workflow_test_config.name,
                    ",".join(self._workflow_test_config.inputs),
                    ",".join(self._workflow_test_config.expected_outputs))

    def _get_test_uuid(self, update=False):
        """
        Get the current UUID or generate a new one.

        :type update: bool
        :param update: ``True`` to force the generation of a new UUID

        :rtype: str
        :return: a generated UUID
        """
        if not self._test_uuid or update:
            self._test_uuid = str(_uuid1())
        return self._test_uuid

    def get_galaxy_workflow(self):
        """
        Return the bioblend workflow instance associated to this runner.

        :rtype: :class:`bioblend.galaxy.objects.wrappers.Workflow`
        :return: bioblend workflow instance
        """
        if not self._galaxy_workflow:
            self._galaxy_workflow = self._workflow_loader.load_workflow(self._workflow_test_config)
        return self._galaxy_workflow

    def run_test(self, base_path=None, inputs=None, expected_outputs=None,
                 output_folder=None, disable_assertions=None, disable_cleanup=None):
        """
        Run the test with the given inputs and expected_outputs.

        :type base_path: str
        :param base_path: base path for workflow and datasets files; the current path is assumed as default

        :type inputs: dict
        :param inputs: a map <INPUT_NAME>:<INPUT_DATASET_INFO> (e.g., {"input_name" : {"file": ...}}

        :type expected_outputs: dict
        :param expected_outputs: maps actual to expected outputs.
               Each output requires a dict containing the path of the expected output filename
               and the fully qualified name of a function which will be used to compare the expected
               to the actual output. Such a function takes ``actual_output_filename`` and ``expected_output_filename``
               as parameters and returns ``True`` if the comparison succeeds, ``False``otherwise.

               Example of expected_outputs:

                    :Example:

                                {'output1': {'comparator': 'filecmp.cmp',
                                             'file': 'change_case_1/expected_output_1',
                                             'name': 'output1'}}

               Comparator function signature:

                    :Example:

                        def compare_outputs(actual_output_filename, expected_output_filename):
                            ....
                            return True | False

        :type output_folder: str
        :param output_folder: the path of folder to temporary store intermediate results

        :type disable_cleanup: bool
        :param disable_cleanup: ``True`` to skip cleanup (Galaxy workflow, history, datasets)
                        after the workflow test execution; ``False`` (default) otherwise.

        :type disable_assertions: bool
        :param disable_assertions: ``True`` to disable assertions during the workflow test execution;
                           ``False`` (default) otherwise.

        :rtype: :class:``WorkflowTestResult``
        :return: workflow test result
        """
        # set basepath
        base_path = self._base_path if not base_path else base_path

        # load workflow
        workflow = self.get_galaxy_workflow()

        # output folder
        if not output_folder:
            output_folder = self._workflow_test_config.output_folder

        # check input_map
        if not inputs:
            if len(self._workflow_test_config.inputs) > 0:
                inputs = self._workflow_test_config.inputs
            else:
                raise ValueError("No input configured !!!")
        # check expected_output_map
        if not expected_outputs:
            if len(self._workflow_test_config.expected_outputs) > 0:
                expected_outputs = self._workflow_test_config.expected_outputs
            else:
                raise ValueError("No output configured !!!")

        # update config options
        disable_cleanup = disable_cleanup if not disable_cleanup is None else self._disable_cleanup
        disable_assertions = disable_assertions if not disable_assertions is None else self._disable_assertions
        output_folder = output_folder if not output_folder is None else self._output_folder

        # uuid of the current test
        test_uuid = self._get_test_uuid(True)

        # store the current message
        error_msg = None

        # check tools
        missing_tools = self.find_missing_tools()
        if len(missing_tools) == 0:

            # create a new history for the current test
            history_info = self._galaxy_history_client.create_history(
                WorkflowTestConfiguration.DEFAULT_HISTORY_NAME_PREFIX + test_uuid)
            history = self._galaxy_instance.histories.get(history_info["id"])
            _logger.info("Create a history '%s' (id: %r)", history.name, history.id)

            # upload input data to the current history
            # and generate the datamap INPUT --> DATASET
            datamap = {}
            for label, config in inputs.items():
                datamap[label] = []
                for filename in config["file"]:
                    datamap[label].append(history.upload_dataset(_os.path.join(base_path, filename)))

            # run the workflow
            _logger.info("Workflow '%s' (id: %s) running ...", workflow.name, workflow.id)
            outputs, output_history = workflow.run(datamap, history, wait=True, polling_interval=0.5)
            _logger.info("Workflow '%s' (id: %s) executed", workflow.name, workflow.id)

            # check outputs
            results, output_file_map = self._check_outputs(base_path, outputs, expected_outputs, output_folder)

            # instantiate the result object
            test_result = _WorkflowTestResult(test_uuid, workflow, inputs, outputs, output_history,
                                              expected_outputs, missing_tools, results, output_file_map,
                                              output_folder)
            if test_result.failed():
                error_msg = "The actual output{0} {2} differ{1} from the expected one{0}." \
                    .format("" if len(test_result.failed_outputs) == 1 else "s",
                            "" if len(test_result.failed_outputs) > 1 else "s",
                            ", ".join(["'{0}'".format(n) for n in test_result.failed_outputs]))

        else:
            # instantiate the result object
            test_result = _WorkflowTestResult(test_uuid, workflow, inputs, [], None,
                                              expected_outputs, missing_tools, [], {}, output_folder)
            error_msg = "Some workflow tools are not available in Galaxy: {0}".format(", ".join(missing_tools))

        # store result
        self._test_cases[test_uuid] = test_result
        if self._test_suite:
            self._test_suite._add_test_result(test_result)

        # cleanup
        if not disable_cleanup:
            self.cleanup()

        # raise error message
        if error_msg:
            _logger.error(error_msg)
            if not disable_assertions:
                raise AssertionError(error_msg)

        return test_result

    def find_missing_tools(self, workflow=None):
        """
        Find tools required by the workflow to test and not installed in the configured Galaxy server.

        :type workflow: :class:`bioblend.galaxy.objects.wrappers.Workflow`
        :param workflow: an optional instance of :class:`bioblend.galaxy.objects.wrappers.Workflow`

        :rtype: list
        :return: the list of missing tools
        """
        _logger.debug("Checking required tools ...")
        workflow = self.get_galaxy_workflow() if not workflow else workflow
        available_tools = self._galaxy_instance.tools.list()
        missing_tools = []
        for order, step in workflow.steps.items():
            if step.tool_id and len(
                    filter(lambda t: t.id == step.tool_id and t.version == step.tool_version, available_tools)) == 0:
                missing_tools.append((step.tool_id, step.tool_version))
        _logger.debug("Missing tools: {0}".format("None"
                                                  if len(missing_tools) == 0
                                                  else ", ".join(["{0} (version {1})"
                                                                 .format(x[0], x[1]) for x in missing_tools])))
        _logger.debug("Checking required tools: DONE")
        return missing_tools

    def _check_outputs(self, base_path, actual_outputs, expected_output_map, output_folder):
        """
        Private method responsible for comparing actual to current outputs

        :param base_path:
        :param actual_outputs:
        :param expected_output_map:
        :param output_folder:

        :rtype: tuple
        :return: a tuple containing a :class:`WorkflowTestResult` as first element
                 and a map <OUTPUT_NAME>:<ACTUAL_OUTPUT_FILENAME> as a second.
        """
        results = {}
        output_file_map = {}

        if not _os.path.isdir(output_folder):
            _os.makedirs(output_folder)

        _logger.info("Checking test output: ...")
        for output in actual_outputs:
            if output.name in expected_output_map:
                _logger.debug("Checking OUTPUT '%s' ...", output.name)
                output_filename = _os.path.join(output_folder, "output_" + str(actual_outputs.index(output)))
                with open(output_filename, "w") as out_file:
                    output.download(out_file)
                    output_file_map[output.name] = {"dataset": output, "filename": output_filename}
                    _logger.debug(
                        "Downloaded output {0}: dataset_id '{1}', filename '{2}'".format(output.name, output.id,
                                                                                         output_filename))
                config = expected_output_map[output.name]
                comparator_fn = config.get("comparator", None)
                _logger.debug("Configured comparator function: %s", comparator_fn)
                comparator = _load_comparator(comparator_fn) if comparator_fn else base_comparator
                if comparator:
                    expected_output_filename = _os.path.join(base_path, config["file"])
                    result = comparator(output_filename, expected_output_filename)
                    _logger.debug(
                        "Output '{0}' {1} the expected: dataset '{2}', actual-output '{3}', expected-output '{4}'"
                            .format(output.name, "is equal to" if result else "differs from",
                                    output.id, output_filename, expected_output_filename))
                    results[output.name] = result
                _logger.debug("Checking OUTPUT '%s': DONE", output.name)
        _logger.info("Checking test output: DONE")
        return (results, output_file_map)

    def cleanup(self):
        for test_uuid, test_result in self._test_cases.items():
            if test_result.output_history:
                self._galaxy_instance.histories.delete(test_result.output_history.id)
            self.cleanup_output_folder(test_result)
        if self._galaxy_workflow:
            self._workflow_loader.unload_workflow(self._galaxy_workflow.id)
            self._galaxy_workflow = None

    def cleanup_output_folder(self, test_result=None):
        test_results = self._test_cases.values() if not test_result else [test_result]
        for _test in test_results:
            for output_name, output_map in _test.output_file_map.items():
                _logger.debug("Cleaning output folder: %s", output_name)
                if _os.path.exists(output_map["filename"]):
                    _os.remove(output_map["filename"])
                    _logger.debug("Deleted output file '%s'.", output_map["filename"])


class _WorkflowTestResult():
    """
    Class for representing the result of a workflow test.
    """

    def __init__(self, test_id, workflow, inputs, outputs, output_history, expected_outputs,
                 missing_tools, results, output_file_map,
                 output_folder=WorkflowTestConfiguration.DEFAULT_OUTPUT_FOLDER):
        self.test_id = test_id
        self.workflow = workflow
        self.inputs = inputs
        self.outputs = outputs
        self.output_history = output_history
        self.expected_outputs = expected_outputs
        self.output_folder = output_folder
        self.missing_tools = missing_tools
        self.output_file_map = output_file_map
        self.results = results

        self.failed_outputs = {out[0]: out[1]
                               for out in self.results.items()
                               if not out[1]}

    def __str__(self):
        return "Test {0}: workflow {1}, intputs=[{2}], outputs=[{3}]" \
            .format(self.test_id, self.workflow.name,
                    ",".join([i for i in self.inputs]),
                    ", ".join(["{0}: {1}".format(x[0], "OK" if x[1] else "ERROR")
                               for x in self.results.items()]))

    def __repr__(self):
        return self.__str__()

    def failed(self):
        """
        Assert whether the test is failed.

        :rtype: bool
        :return: ``True`` if the test is failed; ``False``otherwise.
        """
        return len(self.failed_outputs) > 0

    def passed(self):
        """
        Assert whether the test is passed.

        :rtype: bool
        :return: ``True`` if the test is passed; ``False``otherwise.
        """
        return not self.failed()

    def check_output(self, output):
        """
        Assert whether the actual `output` is equal to the expected accordingly
        to its associated `comparator` function.

        :type output: str or dict
        :param output: output name

        :rtype: bool
        :return: ``True`` if the test is passed; ``False``otherwise.
        """
        return self.results[output if isinstance(output, str) else output.name]

    def check_outputs(self):
        """
        Return a map of pairs <OUTPUT_NAME>:<RESULT>, where <RESULT> is ``True``
        if the actual `OUTPUT_NAME` is equal to the expected accordingly
        to its associated `comparator` function.

        :rtype: dict
        :return: map of output results
        """
        return self.results


def _get_galaxy_instance(galaxy_url=None, galaxy_api_key=None):
    """
    Private utility function to instantiate and configure a :class:`bioblend.GalaxyInstance`

    :type galaxy_url: str
    :param galaxy_url: the URL of the Galaxy server

    :type galaxy_api_key: str
    :param galaxy_api_key: a registered Galaxy API KEY

    :rtype: :class:`bioblend.GalaxyInstance`
    :return: a new :class:`bioblend.GalaxyInstance` instance
    """
    if not galaxy_url:
        if ENV_KEY_GALAXY_URL in _os.environ:
            galaxy_url = _os.environ[ENV_KEY_GALAXY_URL]
        else:
            raise ValueError("GALAXY URL not defined!!!")
    # set the galaxy api key
    if not galaxy_api_key:
        if ENV_KEY_GALAXY_API_KEY in _os.environ:
            galaxy_api_key = _os.environ[ENV_KEY_GALAXY_API_KEY]
        else:
            raise ValueError("GALAXY API KEY not defined!!!")
    # initialize the galaxy instance
    return _GalaxyInstance(galaxy_url, galaxy_api_key)


def _load_configuration(config_filename):
    with open(config_filename) as config_file:
        workflows_conf = _yaml_load(config_file)
        for wf_name, wf in workflows_conf["workflows"].items():
            wf["inputs"] = _parse_dict(wf["inputs"])
            wf["expected"] = _parse_dict(wf["expected"])
    return workflows_conf


def _parse_dict(elements):
    results = {}
    for name, value in elements.items():
        result = value
        if isinstance(value, str):
            result = {"name": name, "file": value}
        elif isinstance(value, dict):
            result["name"] = name
        else:
            raise ValueError("Configuration error: %r", elements)
        results[name] = result
    return results


def _load_comparator(fully_qualified_comparator_function):
    """
    Utility function responsible for dynamically loading a comparator function
    given its fully qualified name.

    :type fully_qualified_comparator_function: str
    :param fully_qualified_comparator_function: fully qualified name of a comparator function

    :return: a callable reference to the loaded comparator function
    """
    mod = None
    try:
        components = fully_qualified_comparator_function.split('.')
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
    except ImportError, e:
        _logger.error(e)
    except AttributeError, e:
        _logger.error(e)
    except:
        _logger.error("Unexpected error:", _exc_info()[0])
    return mod


def base_comparator(actual_output_filename, expected_output_filename):
    _logger.debug("Using default comparator....")
    with open(actual_output_filename) as aout, open(expected_output_filename) as eout:
        diff = _unified_diff(aout.readlines(), eout.readlines(), actual_output_filename, expected_output_filename)
        ldiff = list(diff)
        if len(ldiff) > 0:
            print "\n{0}\n...\n".format("".join(ldiff[:20]))
        return len(ldiff) == 0


def _parse_cli_options():
    parser = _optparse.OptionParser()
    parser.add_option('--server', help='Galaxy server URL')
    parser.add_option('--api-key', help='Galaxy server API KEY')
    parser.add_option('--enable-logger', help='Enable log messages', action='store_true')
    parser.add_option('--debug', help='Enable debug mode', action='store_true')
    parser.add_option('--disable-cleanup', help='Disable cleanup', action='store_true')
    parser.add_option('--disable-assertions', help='Disable assertions', action='store_true')
    parser.add_option('-o', '--output', help='absolute path of the folder where output is written')
    parser.add_option('-f', '--file', default=WorkflowTestConfiguration.DEFAULT_CONFIG_FILENAME,
                      help='YAML configuration file of workflow tests')
    (options, args) = parser.parse_args()
    return (options, args)


def run_tests(enable_logger=None, enable_debug=None, disable_cleanup=None, disable_assertions=None):
    """
    Run a workflow test suite defined in a configuration file.

    :type enable_logger: bool
    :param enable_logger: enable logger (disabled by default)

    :type enable_debug: bool
    :param enable_debug: enable debug messages (disabled by default)

    :type disable_cleanup: bool
    :param disable_cleanup: ``True`` to skip cleanup (Galaxy workflow, history, datasets)
                            after the workflow test execution; ``False`` (default) otherwise.

    :type disable_assertions: bool
    :param disable_assertions: ``True`` to disable assertions during the workflow test execution;
           ``False`` (default) otherwise.

    :rtype: tuple
    :return: a tuple (test_suite_instance,suite_configuration)
    """
    options, args = _parse_cli_options()
    config = WorkflowTestConfiguration.load(options.file)

    config["galaxy_url"] = options.server \
        if options.server \
        else config["galaxy_url"] if "galaxy_url" in config else None

    config["galaxy_api_key"] = options.api_key \
        if options.api_key \
        else config["galaxy_api_key"] if "galaxy_api_key" in config else None

    config["output_folder"] = options.output \
        if options.output \
        else config["output_folder"] if "output_folder" in config \
        else WorkflowTestConfiguration.DEFAULT_OUTPUT_FOLDER

    config["enable_logger"] = enable_logger or options.enable_logger or config.get("enable_logger", False)
    config["enable_debug"] = enable_debug or options.debug or config.get("enable_debug", False)
    config["disable_cleanup"] = disable_cleanup or options.disable_cleanup or config.get("disable_cleanup", False)
    config["disable_assertions"] = disable_assertions or options.disable_assertions \
                                   or config.get("disable_assertions", False)

    for test_config in config["workflows"].values():
        test_config.disable_cleanup = config["disable_cleanup"]
        test_config.disable_assertions = config["disable_assertions"]

    # enable the logger with the proper detail level
    if config["enable_logger"] or config["enable_debug"]:
        config["logger_level"] = _logging.DEBUG if config["enable_debug"] else _logging.INFO
        _logger.setLevel(config["logger_level"])

    # log the current configuration
    _logger.info("Configuration: %r", config)

    # create and run the configured test suite
    test_suite = WorkflowTestSuite(config["galaxy_url"], config["galaxy_api_key"])
    test_suite.run_test_suite(config)

    return (test_suite, config)


if __name__ == '__main__':
    run_tests()
