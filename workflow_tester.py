#!/usr/bin/env python

import os as _os

import logging as _logging
import unittest as _unittest
import optparse as _optparse

from json import load as _json_load
from yaml import load as _yaml_load
from uuid import uuid1 as  _uuid1

from bioblend.galaxy.objects import GalaxyInstance as _GalaxyInstance
from bioblend.galaxy.workflows import WorkflowClient as _WorkflowClient
from bioblend.galaxy.histories import HistoryClient as _HistoryClient

# Galaxy ENV variable names
ENV_KEY_GALAXY_URL = "BIOBLEND_GALAXY_URL"
ENV_KEY_GALAXY_API_KEY = "BIOBLEND_GALAXY_API_KEY"

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

# configure logger
_logger = _logging.getLogger("WorkflowTest")
_logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')


class WorkflowTestSuite():
    def __init__(self, galaxy_url=None, galaxy_api_key=None):
        self._workflows = {}
        self._workflows_tests = []
        self._galaxy_instance = None
        self._galaxy_workflow_client = None
        #
        if galaxy_url:
            self._galaxy_url = galaxy_url
        elif _os.environ.has_key(ENV_KEY_GALAXY_URL):
            self._galaxy_url = _os.environ[ENV_KEY_GALAXY_URL]
        else:
            raise ValueError("GALAXY URL not defined!!!")
        #
        if galaxy_api_key:
            self._galaxy_api_key = galaxy_api_key
        elif _os.environ.has_key(ENV_KEY_GALAXY_API_KEY):
            self._galaxy_api_key = _os.environ[ENV_KEY_GALAXY_API_KEY]
        else:
            raise ValueError("GALAXY API KEY not defined!!!")

        # initialize the galaxy instance
        self._galaxy_instance = _GalaxyInstance(self._galaxy_url, self._galaxy_api_key)
        self._galaxy_workflow_client = _WorkflowClient(self._galaxy_instance.gi)

    @property
    def galaxy_url(self):
        return self._galaxy_url

    @property
    def galaxy_api_key(self):
        return self._galaxy_api_key

    @property
    def galaxy_instance(self):
        return self._galaxy_instance

    @property
    def workflows(self):
        return self.galaxy_instance.workflows.list()

    def run_tests(self, workflow_tests_config):
        results = []
        for test_config in workflow_tests_config["workflows"].values():
            workflow = self.create_test_runner(test_config)
            test_case = workflow.run_test(test_config["inputs"], test_config["outputs"],
                                          workflow_tests_config["output_folder"])
            results.append(test_case)
        return results

    def run_test_suite(self, workflow_tests_config):
        suite = _unittest.TestSuite()
        for test_config in workflow_tests_config["workflows"].values():
            workflow = self.create_test_runner(test_config)
            suite.addTest(workflow)
        _RUNNER = _unittest.TextTestRunner(verbosity=2)
        _RUNNER.run((suite))
        # cleanup
        if not workflow_tests_config["disable_cleanup"]:
            self.cleanup()

    def create_test_runner(self, workflow_test_config):
        workflow_filename = workflow_test_config["file"] \
            if not workflow_test_config.has_key("base_path") \
            else _os.path.join(workflow_test_config["base_path"], workflow_test_config["file"])
        workflow = self._load_work_flow(workflow_filename, workflow_test_config["name"])
        runner = WorkflowTestRunner(self.galaxy_instance, workflow, workflow_test_config)
        self._workflows_tests.append(runner)
        return runner

    def cleanup(self):
        _logger.debug("Cleaning save histories ...")
        hslist = self.galaxy_instance.histories.list()
        for history in [h for h in hslist if DEFAULT_HISTORY_NAME_PREFIX in h.name]:
            self.galaxy_instance.histories.delete(history.id)

        _logger.debug("Cleaning workflow library ...")
        wflist = self.galaxy_instance.workflows.list()
        workflows = [w for w in wflist if DEFAULT_WORKFLOW_NAME_PREFIX in w.name]
        for wf in workflows:
            self._unload_workflow(wf.id)

    def _load_work_flow(self, workflow_filename, workflow_name=None):
        with open(workflow_filename) as f:
            wf_json = _json_load(f)
        if not self._workflows.has_key(wf_json["name"]):
            wf_name = wf_json["name"]
            wf_json["name"] = workflow_name if workflow_name else "_".join([DEFAULT_WORKFLOW_NAME_PREFIX, wf_name])
            wf_info = self._galaxy_workflows.import_workflow_json(wf_json)
            workflow = self.galaxy_instance.workflows.get(wf_info["id"])
            self._workflows[wf_name] = workflow
        else:
            workflow = self._workflows[wf_json["name"]]
        return workflow

    def _unload_workflow(self, workflow_id):
        self._galaxy_workflows.delete_workflow(workflow_id)


class WorkflowTestRunner(_unittest.TestCase):
    def __init__(self, galaxy_instance, galaxy_workflow, workflow_test_config):

        self._galaxy_instance = galaxy_instance
        self._workflow_test_config = workflow_test_config
        self._galaxy_workflow = galaxy_workflow
        self._galaxy_history_client = _HistoryClient(galaxy_instance.gi)
        self._disable_cleanup = workflow_test_config.get("disable_cleanup", False)
        self._disable_assertions = workflow_test_config.get("disable_assertions", False)
        self._base_path = workflow_test_config.get("base_path", "")
        self._test_cases = {}
        self._test_uuid = None

        setattr(self, "test_" + workflow_test_config["name"], self.run_test)
        super(WorkflowTestRunner, self).__init__("test_" + workflow_test_config["name"])

    def __str__(self):
        return "Workflow Test '{0}': testId={1}, workflow='{2}', input=[{3}], output=[{4}]" \
            .format(self._workflow_test_config["name"],
                    self._get_test_uuid(),
                    self._workflow_test_config["name"],
                    ",".join(self._workflow_test_config[
                                 "inputs"]),
                    ",".join(self._workflow_test_config[
                                 "outputs"]))

    def _get_test_uuid(self, update=False):
        if not self._test_uuid or update:
            self._test_uuid = str(_uuid1())
        return self._test_uuid

    def find_missing_tools(self):
        _logger.debug("Checking required tools ...")
        available_tools = self._galaxy_instance.tools.list()
        missing_tools = []
        for order, step in self._galaxy_workflow.steps.items():
            if step.tool_id and len(
                    filter(lambda t: t.id == step.tool_id and t.version == step.tool_version, available_tools)) == 0:
                missing_tools.append((step.tool_id, step.tool_version))
        _logger.debug("Missing tools: {0}".format("None"
                                                  if len(missing_tools) == 0
                                                  else ", ".join(["{0} (version {1})"
                                                                 .format(x[0], x[1]) for x in missing_tools])))
        _logger.debug("Checking required tools: DONE")
        return missing_tools

    def run_test(self, base_path=None, input_map=None, expected_output_map=None,
                 output_folder=DEFAULT_OUTPUT_FOLDER, assertions=None, cleanup=None):

        # set basepath
        base_path = self._base_path if not base_path else base_path

        # check input_map
        if not input_map:
            if self._workflow_test_config.has_key("inputs"):
                input_map = self._workflow_test_config["inputs"]
            else:
                raise ValueError("No input configured !!!")
        # check expected_output_map
        if not expected_output_map:
            if self._workflow_test_config.has_key("outputs"):
                expected_output_map = self._workflow_test_config["outputs"]
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
            history_info = self._galaxy_history_client.create_history(DEFAULT_HISTORY_NAME_PREFIX + test_uuid)
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
            _logger.info("Workflow '%s' (id: %s) running ...", self._galaxy_workflow.name, self._galaxy_workflow.id)
            outputs, output_history = self._galaxy_workflow.run(datamap, history, wait=True, polling_interval=0.5)
            _logger.info("Workflow '%s' (id: %s) executed", self._galaxy_workflow.name, self._galaxy_workflow.id)

            # check outputs
            results, output_file_map = self._check_outputs(base_path, outputs, expected_output_map, output_folder)

            # instantiate the result object
            test_result = WorkflowTestResult(test_uuid, self._galaxy_workflow, input_map, outputs, output_history,
                                             expected_output_map, missing_tools, results, output_file_map,
                                             output_folder)
            if test_result.failed():
                error_msg = "Some outputs differ from the expected ones: {0}".format(
                    ", ".join(test_result.failed_outputs))

        else:
            # instantiate the result object
            test_result = WorkflowTestResult(test_uuid, self._galaxy_workflow, input_map, [], None,
                                             expected_output_map, missing_tools, [], {}, output_folder)
            error_msg = "Some workflow tools are not available in Galaxy: {0}".format(", ".join(missing_tools))

        # store
        self._test_cases[test_uuid] = test_result

        # cleanup
        if not disable_cleanup:
            self.cleanup()

        # raise error message
        if error_msg:
            _logger.error(error_msg)
            if not disable_assertions:
                raise AssertionError(error_msg)

        return test_result

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
        for test_id, test_case in self._test_cases.items():
            test_case.cleanup()


class WorkflowTestResult():
    def __init__(self, test_id, workflow, input_map, outputs, output_history, expected_output_map,
                 missing_tools, results, output_file_map, output_folder=DEFAULT_OUTPUT_FOLDER):
        self.test_id = test_id
        self.workflow = workflow
        self.inputs = input_map
        self.outputs = outputs
        self.output_history = output_history
        self.expected_output_map = expected_output_map
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
        return self.results[output.name]

    def check_outputs(self, force=False):
        return self.results


def load_configuration(filename=DEFAULT_CONFIG_FILENAME):
    config = {}
    if _os.path.exists(filename):
        base_path = _os.path.dirname(_os.path.abspath(filename))
        with open(filename, "r") as config_file:
            workflows_conf = yaml.load(config_file)
            config["galaxy_url"] = workflows_conf["galaxy_url"]
            config["galaxy_api_key"] = workflows_conf["galaxy_api_key"]
            config["workflows"] = {}
            for workflow in workflows_conf.get("workflows").items():
                w = DEFAULT_WORKFLOW_CONFIG.copy()
                w["name"] = workflow[0]
                w.update(workflow[1])
                # parse inputs
                w["inputs"] = _parse_yaml_list(w["inputs"])
                # parse outputs
                w["outputs"] = _parse_yaml_list(w["outputs"])
                # add base path
                w["base_path"] = base_path
                # add the workflow
                config["workflows"][w["name"]] = w
    else:
        config["workflows"] = {"unknown": DEFAULT_WORKFLOW_CONFIG.copy()}
    return config


def load_workflow_test_configuration(workflow_test_name, filename=DEFAULT_CONFIG_FILENAME):
    config = load_configuration(filename)
    if config["workflows"].has_key(workflow_test_name):
        return config["workflows"][workflow_test_name]
    else:
        raise KeyError("WorkflowTest with name '%s' not found" % workflow_test_name)


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
    parser.add_option('-f', '--file', default=DEFAULT_CONFIG_FILENAME, help='YAML configuration file of workflow tests')
    (options, args) = parser.parse_args()
    return (options, args)


def main(clean_up=True):
    options, args = _parse_cli_options()
    config = load_configuration(options.file)

    config["galaxy_url"] = options.server \
        if options.server \
        else config["galaxy_url"] if config.has_key("galaxy_url") else None

    config["galaxy_api_key"] = options.api_key \
        if options.api_key \
        else config["galaxy_api_key"] if config.has_key("galaxy_api_key") else None

    config["output_folder"] = options.output \
        if options.output \
        else config["output_folder"] if config.has_key("output_folder") else DEFAULT_OUTPUT_FOLDER

    config["enable_logger"] = options.enable_logger \
        if options.enable_logger \
        else config["enable_logger"] if config.has_key("enable_logger") else False

    config["disable_cleanup"] = options.disable_cleanup
    config["disable_assertions"] = options.disable_assertions

    for test_config in config["workflows"].values():
        test_config["disable_cleanup"] = config["disable_cleanup"]
        test_config["disable_assertions"] = config["disable_assertions"]

    # enable the logger with the proper detail level
    if config["enable_logger"]:
        config["logger_level"] = _logging.DEBUG if options.debug else _logging.INFO
        _logger.setLevel(config["logger_level"])

    # log the current configuration
    _logger.debug("Configuration: %r", config)

    # create and run the configured test suite
    test_suite = WorkflowTestSuite(config["galaxy_url"], config["galaxy_api_key"])
    test_suite.run_test_suite(config)

    return (test_suite, config)


if __name__ == '__main__':
    main()
