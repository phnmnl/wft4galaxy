import os as _os
import json as _json
import types as _types
import collections as _collections
import uuid as _uuid

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


class HistoryWrapper(object):
    def __init__(self, wrapped_history):
        super(HistoryWrapper, self).__init__()
        self.wrapped = wrapped_history
        self.gi = wrapped_history.gi
        self.job_tool = {}
        self.creating_jobs = {}
        self.datasets = None
        self.dataset_index = {}
        self.input_datasets = {}
        self.output_datasets = {}
        # TODO: to properly initialize
        self.output_labels = {}
        self.intermediate_outputs = {}
        self.dataset_input_of = {}

        # process history
        self._init()

    def _init(self):
        h = self.wrapped
        datasets = h.get_datasets()
        self.datasets = datasets

        for hd in datasets:
            job_id = hd.wrapped["creating_job"]
            job_info = self.gi.jobs.get(job_id, full_details=True)
            self.creating_jobs[hd.id] = job_info
            self.job_tool[hd.id] = self.gi.tools.get(job_info.wrapped["tool_id"], io_details=True)

            # detect whether the DS is an input
            job_inputs = job_info.wrapped["inputs"]
            print("Job inputs %r" % job_inputs)
            if len(job_inputs) == 0:
                print("Input found %r %s" % (hd.id, hd.wrapped["name"]))
                self.input_datasets[hd.id] = hd
            else:
                print("Not an input: %r %s" % (hd.id, hd.wrapped["name"]))
                for ji, jv in job_inputs.items():
                    print("HD %s %s" % (jv["id"], hd.id))
                    if ji not in self.dataset_input_of:
                        self.dataset_input_of[jv["id"]] = []
                    self.dataset_input_of[jv["id"]].append(hd.id)

        # detect whether the DS is an output
        for hd in datasets:
            # print("Checking %s" % hd.id)
            if hd.id not in self.dataset_input_of:
                print("Output found:  %r %s" % (hd.id, hd.wrapped["name"]))
                self.output_datasets[hd.id] = hd
            elif hd.id not in self.input_datasets:
                print("Intermediary output %r" % hd.id)
                self.intermediate_outputs[hd.id] = hd
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
