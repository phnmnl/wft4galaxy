class WorkflowTestRunner(_unittest.TestCase):
    """
    Class responsible for launching a workflow test.
    """

    def __init__(self, galaxy_instance, workflow_loader, workflow_test_config, test_suite=None):
        self._galaxy_instance = galaxy_instance
        self._workflow_loader = workflow_loader
        self._workflow_test_config = workflow_test_config
        self._test_suite = test_suite
        self._disable_cleanup = workflow_test_config.disable_cleanup
        self._disable_assertions = workflow_test_config.disable_assertions
        self._output_folder = workflow_test_config.output_folder
        self._base_path = workflow_test_config.base_path
        self._test_cases = {}
        self._test_uuid = None
        self._galaxy_workflow = None
        self._file_handler = None
        self.test_result = None

        setattr(self, "test_" + workflow_test_config.name, self.run_test)
        super(WorkflowTestRunner, self).__init__("test_" + workflow_test_config.name)

    @property
    def workflow_test_config(self):
        """
        :rtype: :class:`WorkflowTestCase`
        :return: the :class:`WorkflowTestCase` instance associated to this runner
        """
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
        Return the :class:`bioblend.galaxy.objects.wrappers.Workflow` instance associated to this runner.

        :rtype: :class:`bioblend.galaxy.objects.wrappers.Workflow`
        :return: a :class:`bioblend.galaxy.objects.wrappers.Workflow` instance
        """
        if not self._galaxy_workflow:
            self._galaxy_workflow = self._workflow_loader.load_workflow(
                self._workflow_test_config,
                workflow_name_prefix=_core.WorkflowTestCase.DEFAULT_WORKFLOW_NAME_PREFIX)
        return self._galaxy_workflow

    def run_test(self, base_path=None, inputs=None, params=None, expected_outputs=None,
                 output_folder=None, disable_assertions=None, disable_cleanup=None,
                 enable_logger=None, enable_debug=None):
        """
        Run the workflow test which this runner is associated to.
        The parameters ``base_path``, ``inputs``, ``outputs``, ``expected_outputs``
        ``output_folder``, ``disable_assertions``, ``disable_cleanup``, ``enable_logger``, ``enable_debug``
        can be provided to override the corresponding defined in the :class:`WorkflowTestCase` instance
        which this runner is related to (see :class:`WorkflowTestCase` for more details).

        :rtype: :class:`WorkflowTestResult`
        :return: the :class:`WorkflowTestResult` instance which represents the test result
        """

        _logger.debug("TestCase configuration: %r", self._workflow_test_config.__dict__)

        # update test settings
        if enable_logger is None \
                and self._workflow_test_config is not None \
                and hasattr(self._workflow_test_config, "enable_logger"):
            enable_logger = self._workflow_test_config.enable_logger
        if enable_debug is None \
                and self._workflow_test_config is not None \
                and hasattr(self._workflow_test_config, "enable_debug"):
            enable_debug = self._workflow_test_config.enable_debug
        if disable_cleanup is None:
            disable_cleanup = self._workflow_test_config.disable_cleanup
        if disable_assertions is None:
            disable_assertions = self._workflow_test_config.disable_assertions

        # set basepath
        base_path = self._base_path if not base_path else base_path

        # load workflow
        workflow = self.get_galaxy_workflow()

        # output folder
        if output_folder is None:
            output_folder = self._workflow_test_config.output_folder

        # update logger
        if enable_logger or enable_debug:
            _common.LoggerManager.update_log_level(_logging.DEBUG if enable_debug else _logging.INFO)
            if disable_cleanup:
                self._file_handler = _common.LoggerManager.enable_log_to_file(output_folder=output_folder)
        else:
            _common.LoggerManager.update_log_level(_logging.ERROR)

        # check input_map
        if inputs is None:
            if len(self._workflow_test_config.inputs) > 0:
                inputs = self._workflow_test_config.inputs
            else:
                raise ValueError("No input configured !!!")

        # check params
        if params is None:
            params = self._workflow_test_config.params
            _logger.debug("Using default params")

        # check expected_output_map
        if expected_outputs is None:
            if len(self._workflow_test_config.expected_outputs) > 0:
                expected_outputs = self._workflow_test_config.expected_outputs
            else:
                raise ValueError("No output configured !!!")

        # update config options
        disable_cleanup = disable_cleanup if disable_cleanup is not None else self._disable_cleanup
        disable_assertions = disable_assertions if disable_assertions is not None else self._disable_assertions
        output_folder = output_folder if output_folder is not None else self._output_folder

        # uuid of the current test
        test_uuid = self._get_test_uuid(True)

        # store the current message
        error_msg = None

        # test restul
        test_result = None

        # check tools
        errors = []
        missing_tools = self.find_missing_tools()
        if len(missing_tools) == 0:

            try:

                # create a new history for the current test
                history = self._galaxy_instance.histories.create(
                    _core.WorkflowTestCase.DEFAULT_HISTORY_NAME_PREFIX + test_uuid)
                _logger.info("Create a history '%s' (id: %r)", history.name, history.id)

                # upload input data to the current history
                # and generate the datamap INPUT --> DATASET
                datamap = {}
                for label, config in _iteritems(inputs):
                    datamap[label] = []
                    for filename in config["file"]:
                        dataset_filename = filename if _os.path.isabs(filename) else _os.path.join(base_path, filename)
                        if config["type"]:
                            datamap[label].append(
                                history.upload_dataset(dataset_filename, file_type=config["type"]))
                        else:
                            datamap[label].append(history.upload_dataset(dataset_filename))

                # run the workflow
                _logger.info("Workflow '%s' (id: %s) running ...", workflow.name, workflow.id)
                outputs, output_history = workflow.run(datamap, history, params=params, wait=True, polling_interval=0.5)
                _logger.info("Workflow '%s' (id: %s) executed", workflow.name, workflow.id)

                # check outputs
                results, output_file_map = self._check_outputs(base_path, outputs, expected_outputs, output_folder)

                # instantiate the result object
                test_result = _core.WorkflowTestResult(test_uuid, workflow, inputs, outputs, output_history,
                                                       expected_outputs, missing_tools, results, output_file_map,
                                                       output_folder)
                if test_result.failed():
                    error_msg = "The actual output{0} {2} differ{1} from the expected one{0}." \
                        .format("" if len(test_result.failed_outputs) == 1 else "s",
                                "" if len(test_result.failed_outputs) > 1 else "s",
                                ", ".join(["'{0}'".format(n) for n in test_result.failed_outputs]))

            except RuntimeError as e:
                error_msg = "Runtime error: {0}".format(e.message)
                errors.append(error_msg)
                _logger.debug(error_msg)

        else:
            error_msg = "Some workflow tools are not available in Galaxy: {0}".format(
                ", ".join(["{0} (ver. {1})".format(t[0], t[1]) for t in missing_tools]))
            errors.append(error_msg)
            _logger.debug(error_msg)

        # instantiate the result object
        if not test_result:
            test_result = _core.WorkflowTestResult(test_uuid, workflow, inputs, [], None,
                                                   expected_outputs, missing_tools, {}, {}, output_folder, errors)

        # store result
        self._test_cases[test_uuid] = test_result
        if self._test_suite:
            self._test_suite._add_test_result(test_result)
        # FIXME
        self.test_result = test_result

        # cleanup
        if not disable_cleanup:
            self.cleanup(output_folder)

        # disable file logger
        if self._file_handler is not None:
            _common.LoggerManager.remove_file_handler(self._file_handler, not disable_cleanup)
            self._file_handler = None

        # raise error message
        if error_msg:
            if not disable_assertions:
                raise AssertionError(error_msg)

        return test_result

    def find_missing_tools(self, workflow=None):
        """
        Find tools required by the workflow to test and not installed on the configured Galaxy server.

        :type workflow: :class:`bioblend.galaxy.objects.wrappers.Workflow`
        :param workflow: an optional instance of :class:`bioblend.galaxy.objects.wrappers.Workflow`

        :rtype: list
        :return: the list of missing tools
        """
        _logger.debug("Checking required tools ...")
        workflow = self.get_galaxy_workflow() if not workflow else workflow
        available_tools = self._galaxy_instance.tools.list()
        missing_tools = []
        _logger.debug("Available tools: %s", ", ".join(["{0}, {1}".format(t.id, t.version) for t in available_tools]))
        for order, step in _iteritems(workflow.steps):
            if step.tool_id and len([t for t in available_tools
                                     if t.id == step.tool_id and t.version == step.tool_version]) == 0:
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
                output_filename = _os.path.join(output_folder, output.name)
                with open(output_filename, "wb") as out_file:
                    output.download(out_file)
                    output_file_map[output.name] = {"dataset": output, "filename": output_filename}
                    _logger.debug(
                        "Downloaded output {0}: dataset_id '{1}', filename '{2}'".format(output.name, output.id,
                                                                                         output_filename))
                config = expected_output_map[output.name]
                comparator_fn = config.get("comparator", None)
                _logger.debug("Configured comparator function: %s", comparator_fn)
                comparator = _comparators.load_comparator(comparator_fn) \
                    if comparator_fn else _comparators.base_comparator
                if comparator:
                    expected_output_filename = config["file"] if _os.path.isabs(config["file"]) \
                        else _os.path.join(base_path, config["file"])
                    result = comparator(output_filename, expected_output_filename)
                    _logger.debug(
                        "Output '{0}' {1} the expected: dataset '{2}', actual-output '{3}', expected-output '{4}'"
                            .format(output.name, "is equal to" if result else "differs from",
                                    output.id, output_filename, expected_output_filename))
                    results[output.name] = result
                _logger.debug("Checking OUTPUT '%s': DONE", output.name)
        _logger.info("Checking test output: DONE")
        return results, output_file_map

    def cleanup(self, output_folder=None):
        """
        Perform a complete clean up of the data produced during the execution of a workflow test,
        i.e., the uploaded workflow and the created history are removed from Galaxy and the actual
        output datasets (downloaded from Galaxy) are deleted from the output path of the local file system.
        """
        _logger.debug("Cleanup of workflow test '%s'...", self._test_uuid)
        for test_uuid, test_result in _iteritems(self._test_cases):
            if test_result.output_history:
                self._galaxy_instance.histories.delete(test_result.output_history.id)
            self.cleanup_output_folder(test_result)
        if self._galaxy_workflow:
            self._workflow_loader.unload_workflow(self._galaxy_workflow.id)
            self._galaxy_workflow = None
        _logger.debug("Cleanup of workflow test '%s': DONE", self._test_uuid)
        if output_folder and _os.path.exists(output_folder):
            _shutil.rmtree(output_folder)
            _logger.debug("Deleted WF output folder '%s': DONE", output_folder)

    def cleanup_output_folder(self, test_result=None):
        """
        Perform a clean up of the temporary files produced during the workflow test execution.
        """
        test_results = self._test_cases.values() if not test_result else [test_result]
        for _test in test_results:
            for output_name, output_map in _iteritems(_test.output_file_map):
                _logger.debug("Cleaning output folder: %s", output_name)
                if _os.path.exists(output_map["filename"]):
                    _os.remove(output_map["filename"])
                    _logger.debug("Deleted output file '%s'.", output_map["filename"])


class WorkflowTestSuiteRunner(_unittest.TestSuite):
    """
    Represent a test suite.
    """

    def __init__(self, galaxy_instance, workflow_loader, suite, filter=None, output_folder=".",
                 enable_logger=None, enable_debug=None, disable_cleanup=None, disable_assertions=None):

        """
        Create an instance of :class:`WorkflowTestSuite`.

        :type galaxy_url: str
        :param galaxy_url: url of your Galaxy server instance.  If ``none``, the environment variable
            ``GALAXY_URL`` is used. An error is raised when such a variable cannot be found.

        :type galaxy_api_key: str
        :param galaxy_api_key: an API key from your Galaxy server instance.  If ``none``, the environment variable
            ``GALAXY_API_KEY`` is used. An error is raised when such a variable cannot be found.
        """

        super(WorkflowTestSuiteRunner, self).__init__()
        self._suite = suite
        self._workflows = {}
        self._workflow_runners = []
        self._workflow_test_results = []
        self._galaxy_instance = None

        # log file handler
        self._file_handler = None
        # initialize the galaxy instance
        self._galaxy_instance = galaxy_instance
        # initialize the workflow loader
        self._workflow_loader = workflow_loader

        self.disable_cleanup = suite.disable_cleanup
        self.disable_assertions = suite.disable_assertions
        self.enable_logger = suite.enable_logger
        self.enable_debug = suite.enable_debug

        _update_config(self, output_folder=output_folder, enable_logger=enable_logger, enable_debug=enable_debug,
                       disable_cleanup=disable_cleanup, disable_assertions=disable_assertions)

        for test_config in suite.workflow_tests.values():
            test_config.disable_assertions = False
            if not filter or len(filter) == 0 or test_config.name in filter:
                runner = self._create_test_runner(test_config,
                                                  enable_logger=enable_logger, enable_debug=enable_debug,
                                                  disable_cleanup=disable_cleanup,
                                                  disable_assertions=disable_assertions)
                self.addTest(runner)

    @property
    def galaxy_instance(self):
        """
        :rtype: :class:`bioblend.galaxy.objects.GalaxyInstance`
        :return: the :class:`bioblend.galaxy.objects.GalaxyInstance` instance used to communicate with a Galaxy server
        """
        return self._galaxy_instance

    @property
    def workflow_loader(self):
        """
        :rtype: :class:`WorkflowTestLoader`
        :return: the :class:`WorkflowTestLoader` instance used by this suite
        """
        return self._workflow_loader

    def _add_test_result(self, test_result):
        """
        Private method to publish a test result.

        :type test_result: :class:'WorkflowTestResult'
        :param test_result: an instance of :class:'WorkflowTestResult'
        """
        self._workflow_test_results.append(test_result)

    def _create_test_runner(self, workflow_test_config,
                            enable_logger=None, enable_debug=None, disable_cleanup=None, disable_assertions=None):
        """
        Private method which creates a test runner associated to this suite.

        :type workflow_test_config: :class:'WorkflowTestConfig'
        :param workflow_test_config:

        :rtype: :class:'WorkflowTestRunner'
        :return: the created :class:'WorkflowTestResult' instance
        """
        # update test config
        _update_config(workflow_test_config,
                       enable_logger=enable_logger, enable_debug=enable_debug,
                       disable_cleanup=disable_cleanup, disable_assertions=disable_assertions)
        # create a new runner instance
        runner = WorkflowTestRunner(self.galaxy_instance, self.workflow_loader, workflow_test_config, self)
        self._workflow_runners.append(runner)
        return runner

    @property
    def test_result(self):
        return self.get_workflow_test_results()

    def get_workflow_test_results(self, workflow_id=None):
        """
        Return the list of :class:`WorkflowTestResult` instances representing the results of
        the workflow tests executed by this suite. Such a list can be filtered by workflow,
        specified as ``workflow_id``.

        :type workflow_id: str
        :param workflow_id: the optional ID of a workflow

        :rtype: list
        :return: a list of :class:`WorkflowTestResult` instances
        """
        return list([w for w in self._workflow_test_results if w.id == workflow_id] if workflow_id
                    else self._workflow_test_results)

    def cleanup(self, output_folder=None):
        """
        Perform the clean up of the workflow and history created on the Galaxy server
        """
        for runner in self._workflow_runners:
            runner.cleanup()
        if self._file_handler is not None:
            _common.LoggerManager.remove_file_handler(self._file_handler, True)
        # remove output folder if empty
        if output_folder and _os.path.exists(output_folder) and \
                _os.path.isdir(output_folder) and len(_os.listdir(output_folder)) == 0:
            try:
                _os.rmdir(output_folder)
                _logger.debug("Deleted empty output folder: '%s'", output_folder)
            except OSError as e:
                _logger.debug("Deleted empty output folder '%s' failed: ", e.message)
