from __future__ import print_function
from past.builtins import basestring as _basestring

import json as _json
import logging as _logging
import os as _os
import types as _types
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
