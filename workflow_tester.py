#!/usr/bin/env python

import os as _os

import logging as _logging
import unittest as _unittest
import optparse as _optparse

from uuid import uuid1 as  _uuid1
from yaml import load as _yaml_load, dump as _yaml_dump
from json import load as _json_load, dump as _json_dump

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
        "outputs": {
            "output1": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output1"},
            "output2": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output2"}
        }
    }

    def __init__(self, base_path=".", filename="workflow.ga", name=None, inputs={}, expected_outputs={},
                 cleanup=True, assertions=True):
        # init properties
        self._base_path = None
        self._filename = None
        self._inputs = {}
        self._expected_outputs = {}

        # set parameters
        self.name = name
        self.set_base_path(base_path)
        self.set_filename(filename)
        self.set_inputs(inputs)
        self.set_expected_outputs(expected_outputs)
        self.disable_cleanup = not cleanup
        self.disable_assertions = not assertions

    def __str__(self):
        return "WorkflowTestConfig: name={0}, file={1}, inputs=[{2}], expected_outputs=[{3}]".format(
            self.name, self.filename, ",".join(self.inputs.keys()), ",".join(self.expected_outputs.keys()))

    def __repr__(self):
        return self.__str__()

    @property
    def base_path(self):
        return self._base_path

    def set_base_path(self, base_path):
        self._base_path = base_path

    @property
    def filename(self):
        return self._filename

    def set_filename(self, filename):
        self._filename = filename

    @property
    def inputs(self):
        return self._inputs

    def set_inputs(self, inputs):
        print inputs
        for name, config in inputs.items():
            self.add_input(name, config["file"])

    def add_input(self, name, file):
        if not name:
            raise ValueError("Input name not defined")
        self._inputs[name] = {"name": name, "file": file if isinstance(file, list) else [file]}

    def remove_input(self, name):
        if name in self._inputs:
            del self._inputs[name]

    def get_input(self, name):
        return self._inputs.get(name, None)

    @property
    def expected_outputs(self):
        return self._expected_outputs

    def set_expected_outputs(self, expected_outputs):
        for name, config in expected_outputs.items():
            self.add_expected_output(name, config["file"], config["comparator"])

    def add_expected_output(self, name, filename, comparator="filecmp.cmp"):
        if not name:
            raise ValueError("Input name not defined")
        self._expected_outputs[name] = {"name": name, "file": filename, "comparator": comparator}

    def remove_expected_output(self, name):
        if name in self._expected_outputs:
            del self._expected_outputs[name]

    def get_expected_output(self, name):
        return self._expected_outputs.get(name, None)

    def to_json(self):
        return dict({
            "name": self.name,
            "file": self.filename,
            "inputs": self.inputs,
            "outputs": self.expected_outputs
        })

    @staticmethod
    def load(filename=DEFAULT_CONFIG_FILENAME, workflow_test_name=None):
        config = {}
        if _os.path.exists(filename):
            base_path = _os.path.dirname(_os.path.abspath(filename))
            with open(filename, "r") as config_file:
                workflows_conf = _yaml_load(config_file)
                config["galaxy_url"] = workflows_conf["galaxy_url"]
                config["galaxy_api_key"] = workflows_conf["galaxy_api_key"]
                config["enable_logger"] = workflows_conf["enable_logger"]
                config["workflows"] = {}
                for wf_name, wf_config in workflows_conf.get("workflows").items():
                    # add the workflow
                    w = WorkflowTestConfiguration(base_path=base_path, filename=wf_config["file"], name=wf_name,
                                                  inputs=wf_config["inputs"], expected_outputs=wf_config["outputs"])
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


class WorkflowLoader:
    _instance = None

    @staticmethod
    def get_instance():
        if not WorkflowLoader._instance:
            WorkflowLoader._instance = WorkflowLoader()
        return WorkflowLoader._instance

    def __init__(self, galaxy_instance=None):
        self._galaxy_instance = galaxy_instance
        self._galaxy_workflow_client = None
        self._workflows = {}
        # if galaxy_instance exists, complete initialization
        if galaxy_instance:
            self.initialize()

    def initialize(self, galaxy_url=None, galaxy_api_key=None):
        if not self._galaxy_instance:
            # initialize the galaxy instance
            self._galaxy_instance = _get_galaxy_instance(galaxy_url, galaxy_api_key)
        # initialize the workflow client
        self._galaxy_workflow_client = _WorkflowClient(self._galaxy_instance.gi)

    def load_workflow(self, workflow_test_config, workflow_name=None):
        workflow_filename = workflow_test_config.filename \
            if not workflow_test_config.base_path \
            else _os.path.join(workflow_test_config.base_path, workflow_test_config.filename)
        return self.load_workflow_by_filename(workflow_filename, workflow_name)

    def load_workflow_by_filename(self, workflow_filename, workflow_name=None):
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
        self._galaxy_workflow_client.delete_workflow(workflow_id)
        # TODO: remove workflow from the list

    def unload_workflows(self):
        for wf_name, wf in self._workflows.items():
            self.unload_workflow(wf[id])


class WorkflowTestSuite():
    def __init__(self, galaxy_url=None, galaxy_api_key=None):
        self._workflows = {}
        self._workflow_runners = []
        self._workflow_test_results = []
        self._galaxy_instance = None
        self._galaxy_workflow_client = None

        # initialize the galaxy instance
        self._galaxy_instance = _get_galaxy_instance(galaxy_url, galaxy_api_key)
        # initialize the workflow loader
        self._workflow_loader = WorkflowLoader(self._galaxy_instance)

    @property
    def galaxy_instance(self):
        return self._galaxy_instance

    @property
    def workflow_loader(self):
        return self._workflow_loader

    def get_workflows(self):
        return self.galaxy_instance.workflows.list()

    def get_workflow_test_results(self, workflow_id=None):
        return list([w for w in self._workflow_test_results if w.id == workflow_id] if workflow_id
                    else self._workflow_test_results)

    def _add_test_result(self, test_result):
        self._workflow_test_results.append(test_result)

    def _create_test_runner(self, workflow_test_config):
        runner = WorkflowTestRunner(self.galaxy_instance, self.workflow_loader, workflow_test_config, self)
        self._workflow_runners.append(runner)
        return runner

    def run_tests(self, workflow_tests_config):
        results = []
        for test_config in workflow_tests_config["workflows"].values():
            runner = self._create_test_runner(test_config)
            result = runner.run_test(test_config["inputs"], test_config["outputs"],
                                     workflow_tests_config["output_folder"])
            results.append(result)
        return results

    def run_test_suite(self, workflow_tests_config):
        suite = _unittest.TestSuite()
        for test_config in workflow_tests_config["workflows"].values():
            runner = self._create_test_runner(test_config)
            suite.addTest(runner)
        _RUNNER = _unittest.TextTestRunner(verbosity=2)
        _RUNNER.run((suite))
        # cleanup
        if not workflow_tests_config["disable_cleanup"]:
            self.cleanup()

    def cleanup(self):
        _logger.debug("Cleaning save histories ...")
        hslist = self.galaxy_instance.histories.list()
        for history in [h for h in hslist if WorkflowTestConfiguration.DEFAULT_HISTORY_NAME_PREFIX in h.name]:
            self.galaxy_instance.histories.delete(history.id)
        _logger.debug("Cleaning workflow library ...")
        wflist = self.galaxy_instance.workflows.list()
        workflows = [w for w in wflist if WorkflowTestConfiguration.DEFAULT_WORKFLOW_NAME_PREFIX in w.name]
        for wf in workflows:
            self._workflow_loader.unload_workflow(wf.id)


class WorkflowTestRunner(_unittest.TestCase):
    def __init__(self, galaxy_instance, workflow_loader, workflow_test_config, test_suite=None):
        self._galaxy_instance = galaxy_instance
        self._workflow_loader = workflow_loader
        self._workflow_test_config = workflow_test_config
        self._test_suite = test_suite
        self._galaxy_history_client = _HistoryClient(galaxy_instance.gi)
        self._disable_cleanup = workflow_test_config.disable_cleanup
        self._disable_assertions = workflow_test_config.disable_assertions
        self._base_path = workflow_test_config.base_path
        self._test_cases = {}
        self._test_uuid = None
        self._galaxy_workflow = None

        setattr(self, "test_" + workflow_test_config.name, self.run_test)
        super(WorkflowTestRunner, self).__init__("test_" + workflow_test_config.name)

    @staticmethod
    def new_instance(workflow_test_config, galaxy_url=None, galaxy_api_key=None):
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
        return "Workflow Test '{0}': testId={1}, workflow='{2}', input=[{3}], output=[{4}]" \
            .format(self._workflow_test_config.name,
                    self._get_test_uuid(),
                    self._workflow_test_config.name,
                    ",".join(self._workflow_test_config.inputs),
                    ",".join(self._workflow_test_config.expected_outputs))

    def _get_test_uuid(self, update=False):
        if not self._test_uuid or update:
            self._test_uuid = str(_uuid1())
        return self._test_uuid

    def get_galaxy_workflow(self):
        if not self._galaxy_workflow:
            self._galaxy_workflow = self._workflow_loader.load_workflow(self._workflow_test_config)
        return self._galaxy_workflow

    def run_test(self, base_path=None, input_map=None, expected_output_map=None,
                 output_folder=WorkflowTestConfiguration.DEFAULT_OUTPUT_FOLDER, assertions=None, cleanup=None):

        # set basepath
        base_path = self._base_path if not base_path else base_path

        # load workflow
        workflow = self.get_galaxy_workflow()

        # check input_map
        if not input_map:
            if len(self._workflow_test_config.inputs) > 0:
                input_map = self._workflow_test_config.inputs
            else:
                raise ValueError("No input configured !!!")
        # check expected_output_map
        if not expected_output_map:
            if len(self._workflow_test_config.expected_outputs) > 0:
                expected_output_map = self._workflow_test_config.expected_outputs
            else:
                raise ValueError("No output configured !!!")

        # update config options
        disable_cleanup = self._disable_cleanup if not cleanup else not cleanup
        disable_assertions = self._disable_assertions if not assertions else not assertions

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
            for label, config in input_map.items():
                datamap[label] = []
                for filename in config["file"]:
                    datamap[label].append(history.upload_dataset(_os.path.join(base_path, filename)))

            # run the workflow
            _logger.info("Workflow '%s' (id: %s) running ...", workflow.name, workflow.id)
            outputs, output_history = workflow.run(datamap, history, wait=True, polling_interval=0.5)
            _logger.info("Workflow '%s' (id: %s) executed", workflow.name, workflow.id)

            # check outputs
            results, output_file_map = self._check_outputs(base_path, outputs, expected_output_map, output_folder)

            # instantiate the result object
            test_result = _WorkflowTestResult(test_uuid, workflow, input_map, outputs, output_history,
                                              expected_output_map, missing_tools, results, output_file_map,
                                              output_folder)
            if test_result.failed():
                error_msg = "The following outputs differ from the expected ones: {0}".format(
                    ", ".join(test_result.failed_outputs))

        else:
            # instantiate the result object
            test_result = _WorkflowTestResult(test_uuid, workflow, input_map, [], None,
                                              expected_output_map, missing_tools, [], {}, output_folder)
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

    def _check_outputs(self, base_path, outputs, expected_output_map, output_folder):
        results = {}
        output_file_map = {}

        if not _os.path.isdir(output_folder):
            _os.makedirs(output_folder)

        _logger.info("Checking test output: ...")
        for output in outputs:
            _logger.debug("Checking OUTPUT '%s' ...", output.name)
            output_filename = _os.path.join(output_folder, "output_" + str(outputs.index(output)))
            with open(output_filename, "w") as out_file:
                output.download(out_file)
                output_file_map[output.name] = {"dataset": output, "filename": output_filename}
                _logger.debug(
                    "Downloaded output {0}: dataset_id '{1}', filename '{2}'".format(output.name, output.id,
                                                                                     output_filename))
            config = expected_output_map[output.name]
            comparator = _load_comparator(config["comparator"])
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
        if self._galaxy_workflow:
            self._workflow_loader.unload_workflow(self._galaxy_workflow.id)
            self._galaxy_workflow = None


class _WorkflowTestResult():
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
        return len(self.failed_outputs) > 0

    def passed(self):
        return not self.failed()

    def check_output(self, output, force=False):
        return self.results[output if isinstance(output, str) else output.name]

    def check_outputs(self, force=False):
        return self.results


def _get_galaxy_instance(galaxy_url=None, galaxy_api_key=None):
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


def _parse_yaml_list(ylist):
    objs = {}
    if isinstance(ylist, list):
        for obj in ylist:
            obj_data = obj.items()
            obj_name = obj_data[0][0]
            obj_file = obj_data[0][1]
            objs[obj_name] = {
                "name": obj_name,
                "file": obj_file
            }
    elif isinstance(ylist, dict):
        for obj_name, obj_data in ylist.items():
            obj_data["name"] = obj_name
            objs[obj_name] = obj_data
    return objs


def _load_comparator(fully_qualified_comparator_function):
    components = fully_qualified_comparator_function.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def _parse_cli_options():
    parser = _optparse.OptionParser()
    parser.add_option('--server', help='Galaxy server URL')
    parser.add_option('--api-key', help='Galaxy server API KEY')
    parser.add_option('--enable-logger', help='Enable log messages', action='store_true')
    parser.add_option('--debug', help='Enable debug mode', action='store_true')
    parser.add_option('--disable-cleanup', help='Disable cleanup', action='store_false')
    parser.add_option('--disable-assertions', help='Disable assertions', action='store_false')
    parser.add_option('-o', '--output', help='absolute path of the folder to download workflow outputs')
    parser.add_option('-f', '--file', default=WorkflowTestConfiguration.DEFAULT_CONFIG_FILENAME,
                      help='YAML configuration file of workflow tests')
    (options, args) = parser.parse_args()
    return (options, args)


def run_tests(config=None, debug=None, cleanup=None, assertions=None):
    options, args = _parse_cli_options()
    config = WorkflowTestConfiguration.load(options.file) if not config else config

    config["galaxy_url"] = options.server \
        if options.server \
        else config["galaxy_url"] if "galaxy_url" in config else None

    config["galaxy_api_key"] = options.api_key \
        if options.api_key \
        else config["galaxy_api_key"] if "galaxy_api_key" in config else None

    config["output_folder"] = options.output \
        if options.output \
        else config["output_folder"] if "output_folder" in config else WorkflowTestConfiguration.DEFAULT_OUTPUT_FOLDER

    config["enable_logger"] = True if options.enable_logger else config.get("enable_logger", False)
    config["debug"] = options.debug if not debug else debug
    config["disable_cleanup"] = options.disable_cleanup if not cleanup else cleanup
    config["disable_assertions"] = options.disable_assertions if not assertions else assertions

    for test_config in config["workflows"].values():
        test_config.disable_cleanup = config["disable_cleanup"]
        test_config.disable_assertions = config["disable_assertions"]

    # enable the logger with the proper detail level
    if config["enable_logger"]:
        config["logger_level"] = _logging.DEBUG if debug or options.debug else _logging.INFO
        _logger.setLevel(config["logger_level"])

    # log the current configuration
    _logger.info("Configuration: %r", config)

    # create and run the configured test suite
    test_suite = WorkflowTestSuite(config["galaxy_url"], config["galaxy_api_key"])
    test_suite.run_test_suite(config)

    return (test_suite, config)


if __name__ == '__main__':
    run_tests()
