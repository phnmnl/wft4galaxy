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

        # set wrapped history and GalaxyInstance
        self._history = wrapped_history
        self._gi = wrapped_history.gi

        # job info
        self.job_tool = {}
        self.creating_jobs = {}

        # datasets
        self.datasets = None
        self.input_datasets = _collections.OrderedDict()
        self.output_datasets = _collections.OrderedDict()
        self.intermediate_datasets = _collections.OrderedDict()

        # map dataset inputs to their order
        self._input_order_map = {}

        # job info
        self._jobs = {}
        self.job_input_ids = {}
        self.job_output_ids = {}
        self.creating_jobs = {}
        self.processing_jobs = _collections.OrderedDict()
        self.processing_job_levels = {}

        # tool cache
        self._tools = {}

        # labels
        self.input_dataset_labels = {}
        self.output_dataset_labels = {}
        self.intermediate_dataset_labels = {}

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
    @property
    def jobs(self):
        return self._jobs

    def _get_job(self, job_id):
        if job_id not in self._jobs:
            try:
                self._jobs[job_id] = self._gi.jobs.get(job_id, full_details=True)
            except ConnectionError as e:
                raise TestConfigError("Unable to retrieve job info !")
        return self._jobs[job_id]

    @property
    def tools(self):
        return self._tools

    def _get_tool(self, tool_id):
        if not tool_id in self._tools:
            try:
                self._tools[tool_id] = self._gi.tools.get(tool_id, io_details=True)
            except ConnectionError as e:
                raise TestConfigError("Unable to retrieve tool info !")
        return self._tools[tool_id]
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

    def extract_workflow(self, filename=None):
        wf = _collections.OrderedDict({
            "a_galaxy_workflow": "true",
            "annotation": "",
            "format-version": "0.1",
            "name": "Imported Workflow",
            "uuid": str(_uuid.uuid1()),
            "steps": _collections.OrderedDict()
        })

        # processed jobs
        processed_jobs = []

        # map hds to step
        hds_map = {}

        # position
        p_left = 50
        p_top = 0

        # map output id to its name
        output_labels = {}

        # process steps
        for hds_id, hds in self.input_datasets.items():
            job = self.creating_jobs[hds.id]
            index = len(wf["steps"])
            hds_map[hds_id] = index
            input_name = "input_{0}".format(index)
            input_description = ""
            p_top += 100
            wf["steps"][str(index)] = {
                "annotation": "",
                "content_id": None,
                "id": index,
                "input_connections": {},
                "inputs": [
                    {
                        "description": input_description,
                        "name": input_name
                    }
                ],
                "label": None,
                "name": "Input dataset",
                "outputs": [],
                "position": {
                    "left": p_left,
                    "top": p_top
                },
                "tool_errors": None,
                "tool_id": None,
                "tool_state": _json.dumps({"name": input_name}),
                "tool_version": None,
                "type": "data_input",
                "uuid": str(_uuid.uuid1()),
                "workflow_outputs": []
            }
            processed_jobs.append(job.id)
            print processed_jobs

        p_top = p_top - (100 * (len(self.input_datasets) / 2))

        # process intermediate and final steps
        for hds_id, hds in self.intermediate_outputs.items() + self.output_datasets.items():

            job = self.creating_jobs[hds.id]
            if job.id in processed_jobs:
                continue
            tool = self.job_tool[hds_id]

            p_left += 200

            print "Processing {0} node: {1}".format("intermediate" if hds_id in self.intermediate_outputs else "output",
                                                    tool.name)

            # compute params
            params = {"__page__": 0, "__rerun_remap_job_id__": None}
            tool_inputs = {param["name"]: param for param in tool.wrapped["inputs"]}
            for param_name, param_info in job.wrapped["params"].items():
                print "Params", param_name
                if param_name in tool_inputs:
                    params[param_name] = param_info

            # add inputs to tool state and inputs
            inputs = []
            input_connections = {}
            for job_input_name, job_input_info in job.wrapped["inputs"].items():
                print "Input", job_input_name
                params[job_input_name] = _json.dumps({"__class__": "RuntimeValue"})
                inputs.append({
                    "description": "Runtime input value {0}".format(job_input_name),
                    "name": job_input_name
                })
                input_connections[job_input_name] = {
                    "id": hds_map[job_input_info["id"]],
                    "output_name": output_labels[job_input_info["id"]] if job_input_info[
                                                                              "id"] in output_labels else "output"
                }

            # add outputs
            outputs = []
            workflow_outputs = []
            tool_outputs = {param["name"]: param for param in tool.wrapped["outputs"]}
            for job_output_name, job_output_info in job.wrapped["outputs"].items():
                outputs.append({
                    "name": job_output_name,
                    "type": tool_outputs[job_output_name]["format"]
                })
                workflow_outputs.append({
                    "label": job_output_name,
                    "output_name": job_output_name,
                    "uuid": str(_uuid.uuid1())
                })

                output_labels[job_output_info["id"]] = job_output_name

            index = len(wf["steps"])
            hds_map[hds_id] = index

            wf["steps"][str(index)] = {
                "annotation": "",
                "content_id": tool.name,
                "id": index,
                "input_connections": input_connections,
                "inputs": inputs,
                "label": None,
                "name": tool.name,
                "outputs": outputs,
                "position": {
                    "left": p_left,
                    "top": p_top
                },
                "tool_errors": None,
                "tool_id": tool.name,
                "tool_state": _json.dumps(params),
                "tool_version": tool.version,
                "type": "tool",
                "uuid": str(_uuid.uuid1()),
                "workflow_outputs": workflow_outputs
            }
            print tool.name, workflow_outputs
            processed_jobs.append(job.id)
            print processed_jobs

        # TODO: move me!!!!
        self.dataset_index = hds_map
        self.output_labels = output_labels

        # save workflow
        print "Filename", filename
        with open(filename, "w") as fp:
            _json.dump(wf, fp, indent=4)

        return wf


def extract_workflow(history, filename=None):
    hw = HistoryWrapper(history)
    return hw.extract_workflow(filename)


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
