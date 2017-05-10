from __future__ import print_function
from future.utils import iteritems as _iteritems
from past.builtins import basestring as _basestring

import os as _os
import json as _json
import types as _types
import logging as _logging
from enum import IntEnum
import datetime as _datetime

# bioblend dependencies
from bioblend.galaxy.objects import GalaxyInstance as ObjGalaxyInstance

# Galaxy ENV variable names
ENV_KEY_GALAXY_URL = "GALAXY_URL"
ENV_KEY_GALAXY_API_KEY = "GALAXY_API_KEY"

# configure logger



# map `StandardError` to `Exception` to allow compatibility both with Python2 and Python3
RunnerStandardError = Exception
try:
    RunnerStandardError = StandardError
except NameError:
    pass


class TestConfigError(RuntimeError):
    pass


class DynamicObject(dict):
    """ Represents a dynamic object  """

    def __init__(self, initial_properties=None):
        self.__dict__ = self
        if initial_properties:
            self.update(initial_properties)

    def __setattr__(self, name, value):
        if isinstance(value, _types.FunctionType):
            self[name] = _types.MethodType(value, self)
        else:
            super(DynamicObject, self).__setattr__(name, value)


class Configuration(DynamicObject):
    pass


class LoggerManager(object):
    @staticmethod
    def get_string_format(show_logger_name=False):
        return "%(asctime)s [{0}] [%(levelname)+5.5s]  %(message)s".format(
            "%(name)s" if show_logger_name else "wft4galaxy")

    @staticmethod
    def new_log_file(output_folder):
        makedirs(output_folder)
        return _os.path.join(output_folder, "{0}.log".format(
            _datetime.datetime.now().strftime("%Y%m%d@%H%M%S")))

    @staticmethod
    def configure_logging(level=_logging.ERROR, show_logger_name=False,
                          log_to_folder=None, disable_console_output=False):
        root = _logging.getLogger()
        root.propagate = True
        log_format = LoggerManager.get_string_format(show_logger_name)
        if log_to_folder is not None:
            filename = LoggerManager.new_log_file(log_to_folder)
            if disable_console_output:
                _logging.basicConfig(level=level, format=log_format, filename=filename)
            else:
                _logging.basicConfig(level=level, format=log_format)
                LoggerManager.enable_log_to_file(filename)
        else:
            _logging.basicConfig(level=level, format=log_format)

    @staticmethod
    def update_log_level(level):
        root = _logging.getLogger()
        root.setLevel(level)
        log_format = LoggerManager.get_string_format(level == _logging.DEBUG)
        for h in root.handlers:
            h.setFormatter(_logging.Formatter(log_format))

    @staticmethod
    def get_logger(name_or_class):
        if not isinstance(name_or_class, _basestring):
            name_or_class = "{}.{}".format(name_or_class.__module__, name_or_class.__class__.__name__)
        return _logging.getLogger(name_or_class)

    @staticmethod
    def enable_log_to_file(log_filename=None, output_folder=None):
        logger = _logging.getLogger()
        if output_folder is None and log_filename is None:
            raise ValueError("You must provide at least one the arguments: log_filename or output_folder")
        if log_filename is None:
            log_filename = LoggerManager.new_log_file(output_folder)
        elif not _os.path.isabs(log_filename):
            log_filename = _os.path.join(output_folder, log_filename)
        logger.debug("Enabling LOG file: '%s'", log_filename)
        fileHandler = _logging.FileHandler(log_filename)
        log_format = LoggerManager.get_string_format(logger.getEffectiveLevel() == _logging.DEBUG)
        fileHandler.setFormatter(_logging.Formatter(log_format))
        logger.addHandler(fileHandler)
        return fileHandler

    @staticmethod
    def remove_file_handler(handler, remove_file=False):
        logger = _logging.getLogger()
        if isinstance(handler, _logging.FileHandler):
            logger.debug("Removing log file: %s", handler.baseFilename)
            logger.removeHandler(handler)
            handler.close()
            # remove log file
            if remove_file:
                _os.remove(handler.baseFilename)


def pformat(obj):
    return _json.dumps(obj, sort_keys=True, indent=4)


def makedirs(path, check_if_exists=False):
    try:
        _os.makedirs(path)
    except OSError as e:
        if check_if_exists:
            raise OSError(e.message)


def configure_env_galaxy_server_instance(config, options, base_config=None):
    config["galaxy_url"] = options.galaxy_url \
                           or base_config and base_config.get("galaxy_url") \
                           or _os.environ.get(ENV_KEY_GALAXY_URL)
    if not config["galaxy_url"]:
        raise TestConfigError("Galaxy URL not defined!  Use --server or the environment variable {} "
                              "or specify it in the test configuration".format(ENV_KEY_GALAXY_URL))

    config["galaxy_api_key"] = options.galaxy_api_key \
                               or base_config and base_config.get("galaxy_api_key") \
                               or _os.environ.get(ENV_KEY_GALAXY_API_KEY)
    if not config["galaxy_api_key"]:
        raise TestConfigError("Galaxy API key not defined!  Use --api-key or the environment variable {} "
                              "or specify it in the test configuration".format(ENV_KEY_GALAXY_API_KEY))


def get_galaxy_instance(galaxy_url=None, galaxy_api_key=None):
    """
    Private utility function to instantiate and configure a :class:`bioblend.GalaxyInstance`

    :type galaxy_url: str
    :param galaxy_url: the URL of the Galaxy server

    :type galaxy_api_key: str
    :param galaxy_api_key: a registered Galaxy API KEY

    :rtype: :class:`bioblend.objects.GalaxyInstance`
    :return: a new :class:`bioblend.objects.GalaxyInstance` instance
    """
    # configure `galaxy_url`
    if galaxy_url is None:
        if ENV_KEY_GALAXY_URL not in _os.environ:
            raise TestConfigError("Galaxy URL not defined!  Use --server or the environment variable {} "
                                  "or specify it in the test configuration".format(ENV_KEY_GALAXY_URL))
        else:
            galaxy_url = _os.environ[ENV_KEY_GALAXY_URL]

    # configure `galaxy_api_key`
    if galaxy_api_key is None:
        if ENV_KEY_GALAXY_API_KEY not in _os.environ:
            raise TestConfigError("Galaxy API key not defined!  Use --api-key or the environment variable {} "
                                  "or specify it in the test configuration".format(ENV_KEY_GALAXY_API_KEY))
        else:
            galaxy_api_key = _os.environ[ENV_KEY_GALAXY_API_KEY]

    # initialize the galaxy instance
    return ObjGalaxyInstance(galaxy_url, galaxy_api_key)


class WorkflowLoader(object):
    """
    Singleton utility class responsible for loading (unloading) workflows to (from) a Galaxy server.
    """

    _instance = None

    _logger = LoggerManager.get_logger(__name__)

    @classmethod
    def get_instance(cls, galaxy_instance=None):
        """
        Return the singleton instance of this class.

        :rtype: :class:`WorkflowLoader`
        :return: a :class:`WorkflowLoader` instance
        """
        if not WorkflowLoader._instance:
            cls._logger.debug("Creating a new WorflowLoader instance...")
            WorkflowLoader._instance = WorkflowLoader(galaxy_instance)
        elif galaxy_instance:
            cls._logger.debug("Initializing the existing WorkflowLoader instance...")
            WorkflowLoader._instance._initialize(galaxy_instance)
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
        self._galaxy_instance = None
        self._workflows = {}
        # if galaxy_instance exists, complete initialization
        if galaxy_instance:
            self._initialize(galaxy_instance)

    def initialize(self, galaxy_url, galaxy_api_key):
        """
        Initialize the connection to a Galaxy server instance.

        :type galaxy_url: str
        :param galaxy_url: url of your Galaxy server instance.  If ``none``, the environment variable
            ``GALAXY_URL`` is used. An error is raised when such a variable cannot be found.

        :type galaxy_api_key: str
        :param galaxy_api_key: an API key from your Galaxy server instance.  If ``none``, the environment variable
            ``GALAXY_API_KEY`` is used. An error is raised when such a variable cannot be found.
        """
        if not self._galaxy_instance:
            # initialize the galaxy instance
            self._initialize(get_galaxy_instance(galaxy_url, galaxy_api_key))

    def _initialize(self, galaxy_instance):
        if not self._galaxy_instance:
            # initialize the galaxy instance
            self._galaxy_instance = galaxy_instance

    def load_workflow(self, workflow_test_config,
                      workflow_name=None, workflow_name_prefix="", workflow_name_suffix=""):
        """
        Load the workflow defined in a :class:`WorkflowTestConfig` instance to the configured Galaxy server.
        ``workflow_name`` overrides the default workflow name.

        :type workflow_test_config: :class:`WorkflowTestConfig`
        :param workflow_test_config: the instance of  :class:`WorkflowTestCase`
            representing the workflow test configuration

        :type workflow_name: str
        :param workflow_name: an optional name which overrides the default workflow name
        """
        if not self._galaxy_instance:
            raise RuntimeError("WorkflowLoader not initialized")
        workflow_filename = workflow_test_config.filename \
            if not workflow_test_config.base_path or _os.path.isabs(workflow_test_config.filename) \
            else _os.path.join(workflow_test_config.base_path, workflow_test_config.filename)
        return self.load_workflow_by_filename(workflow_filename,
                                              workflow_name, workflow_name_prefix, workflow_name_suffix)

    def load_workflow_by_filename(self, workflow_filename,
                                  workflow_name=None, workflow_name_prefix="", workflow_name_suffix=""):
        """
        Load the workflow defined within the file named as `workflow_filename` to the connected Galaxy server.

        :type workflow_filename: str
        :param workflow_filename: the path of workflow definition file

        :type workflow_name: str
        :param workflow_name: an optional name which overrides the default workflow name
        """
        if not self._galaxy_instance:
            raise RuntimeError("WorkflowLoader not initialized")
        self._logger.debug("Loading workflow definition from file: %s", workflow_filename)
        with open(workflow_filename) as f:
            wf_json = _json.load(f)
        self._logger.debug("Workflow definition loaded from file: done")
        wf_json["name"] = "-".join([workflow_name_prefix,
                                    (workflow_name if workflow_name else wf_json["name"]).replace(" ", ""),
                                    workflow_name_suffix])
        self._logger.debug("Uploading the Workflow to the Galaxy instance ...")
        wf = self._galaxy_instance.workflows.import_new(wf_json)
        self._logger.debug("Uploading the Workflow to the Galaxy instance: done")
        self._workflows[wf.id] = wf
        return wf

    def unload_workflow(self, workflow_id):
        """
        Unload the workflow identified by ``workflow_id`` from the configured Galaxy server.

        :type workflow_id: str
        :param workflow_id: the ID of the workflow to unload from the connected Galaxy server.
        """
        if not self._galaxy_instance:
            raise RuntimeError("WorkflowLoader not initialized")
        self._galaxy_instance.workflows.delete(workflow_id)
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]

    def unload_workflows(self):
        """
        Unload all workflows loaded by this :class:`WorkflowLoader` instance.
        """
        if not self._galaxy_instance:
            raise RuntimeError("WorkflowLoader not initialized")
        for _, wf in _iteritems(self._workflows):
            self.unload_workflow(wf.id)
