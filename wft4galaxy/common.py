import os as _os
import json as _json
import types as _types

# Galaxy ENV variable names
ENV_KEY_GALAXY_URL = "GALAXY_URL"
ENV_KEY_GALAXY_API_KEY = "GALAXY_API_KEY"


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


def _pformat(obj):
    return _json.dumps(obj, sort_keys=True, indent=4)


def make_dirs(path, check_if_exists=False):
    try:
        _os.makedirs(path)
    except OSError as e:
        if check_if_exists:
            raise OSError(e.message)


def _set_galaxy_server_settings(config, options, base_config=None):
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
