from __future__ import print_function

import json as _json
import logging as _logging
import os as _os
import types as _types

# bioblend dependencies
from bioblend.galaxy.objects import GalaxyInstance as ObjGalaxyInstance

# Galaxy ENV variable names
ENV_KEY_GALAXY_URL = "GALAXY_URL"
ENV_KEY_GALAXY_API_KEY = "GALAXY_API_KEY"

# map `StandardError` to `Exception` to allow compatibility both with Python2 and Python3
RunnerStandardError = Exception
try:
    RunnerStandardError = StandardError
except NameError:
    pass

_log_format = '%(asctime)s %(levelname)s: %(message)s'
_logger = _logging.getLogger("WorkflowTest")
_logging.basicConfig(format=_log_format)


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
