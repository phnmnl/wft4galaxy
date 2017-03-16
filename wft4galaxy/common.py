import os as _os
import json as _json
import uuid as _uuid
import types as _types
import operator as _operator

import collections as _collections

# Galaxy ENV variable names
from bioblend import ConnectionError

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
        self._process_history()

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

    def _process_history(self):

        # check if a history has been assigned
        if self._history is None:
            raise RuntimeError("No history found!")

        # auxiliary infos
        ds_input_info = {}
        ds_output_info = {}
        intermediate_datasets = []

        # get history datasets
        history = self._history
        self.datasets = history.get_datasets()

        # process jobs chain (through their created datasets)
        for ds in self.datasets:

            # load job info
            creating_job = self._get_job(ds.wrapped["creating_job"])
            job_inputs = {in_info["id"]: in_name for in_name, in_info in creating_job.wrapped["inputs"].items()}
            job_outputs = {out_info["id"]: out_name for out_name, out_info in creating_job.wrapped["outputs"].items()}
            intermediate_datasets += job_inputs.keys()

            # update auxiliary data info
            for in_id, in_name in job_inputs.items():
                if in_id not in ds_input_info:
                    ds_input_info[in_id] = {}
                ds_input_info[in_id][creating_job.id] = in_name

            for out_id, out_name in job_outputs.items():
                if out_id not in ds_output_info:
                    ds_output_info[out_id] = {}
                ds_output_info[out_id][creating_job.id] = out_name

            # register the job as the creating of this DS
            self.creating_jobs[ds.id] = creating_job

            # detect if the job creates an input DS
            # or it is a processing job
            if len(job_inputs) == 0:
                self.input_datasets[ds.id] = ds
            else:
                # add the processing job
                self.processing_jobs[creating_job.id] = creating_job
                # compute the processing job level
                self.processing_jobs[creating_job.id]
                # update in/out maps
                if creating_job.id not in self.job_input_ids:
                    self.job_input_ids[creating_job.id] = job_inputs.keys()
                    self.job_output_ids[creating_job.id] = job_outputs.keys()

        # Auxiliary function which computes the label for a given dataset
        def __set_label(labels, ds_id, info_matrix, label=None, prefix=None):
            if label is not None:
                labels[ds_id] = label
            elif len(info_matrix[ds_id]) == 1:
                # use job
                labels[ds_id] = info_matrix[ds_id][info_matrix[ds_id].keys()[0]]
            else:
                # use a default label if the same dataset if used by more than one job
                labels[ds_id] = "{0}_{1}".format(prefix, len(labels))

        # process datasets to:
        #  - determine intermediate and output datasets
        #  - determine input/output labels
        for ds in self.datasets:
            if ds.id in self.input_datasets:
                __set_label(self.input_dataset_labels, ds.id, ds_input_info, prefix="input")
                __set_label(self.intermediate_dataset_labels, ds.id, ds_input_info, label="output")
            else:
                if ds.id in intermediate_datasets:
                    self.intermediate_datasets[ds.id] = ds
                    __set_label(self.input_dataset_labels, ds.id, ds_input_info, prefix="input")
                    __set_label(self.intermediate_dataset_labels, ds.id, ds_output_info, prefix="output")
                else:
                    self.output_datasets[ds.id] = ds
                    __set_label(self.output_dataset_labels, ds.id, ds_output_info, prefix="output")

        intermediate_inputs = []
        not_ordered_inputs = self.input_datasets.keys()
        input_datasets = _collections.OrderedDict()

        # determine the job level
        for job_id, job in self.processing_jobs.items():
            self.processing_job_levels[job_id] = self.compute_processing_job_level(job_id)

            print "Ordering: ", not_ordered_inputs
            tool = self._get_tool(job.wrapped["tool_id"])
            ordered_names = [x["name"] for x in tool.wrapped["inputs"]]
            print "Ordered names", ordered_names
            for name in ordered_names:
                print "Name", name, in_id in not_ordered_inputs
                if name in job.wrapped["inputs"]:
                    in_id = job.wrapped["inputs"][name]["id"]
                    if in_id in not_ordered_inputs:
                        input_datasets[in_id] = self.input_datasets[in_id]
                        not_ordered_inputs.remove(in_id)
            intermediate_inputs.extend([x["id"] for x in job.wrapped["outputs"].values()
                                        if x["id"] not in self.output_datasets])

        # copy remaining inputs
        print "Remaining", not_ordered_inputs
        for ds_in in not_ordered_inputs:
            input_datasets[ds_in] = self.input_datasets[ds_in]

        print "Order before: ", self.input_datasets.keys()
        self.input_datasets = input_datasets
        print "Order after: ", self.input_datasets.keys()

        inputs = self.input_datasets.keys() + intermediate_inputs
        self._input_order_map = {x: inputs.index(x) for x in inputs}

    def compute_processing_job_level(self, job_id):
        level = 0
        for job in self.processing_jobs.values():
            print "\nComparing ", job.id, job_id, job.id == job_id, "Target", job_id
            if job.id == job_id:
                break
            dependencies = [x for x in self.job_output_ids[job.id] if x in self.job_input_ids[job_id]]
            print "Intersetct", job_id, self.job_output_ids[job.id], self.job_input_ids[job_id], x
            if len(dependencies) > 0:
                print "Updating level {0} {1}".format(level, self.processing_job_levels[job.id] + 1)
                level = max(level, self.processing_job_levels[job.id] + 1)
        return level

    def extract_workflow(self, filename=None, workflow_name=None, v_step=100, h_step=400):
        if workflow_name is None:
            workflow_name = "Workflow extracted from history {0}".format(self._history.id)
        wf = _collections.OrderedDict({
            "a_galaxy_workflow": "true",
            "annotation": "",
            "format-version": "0.1",
            "name": workflow_name,
            "uuid": str(_uuid.uuid1()),
            "steps": _collections.OrderedDict()
        })

        # position
        p_left = 50
        p_top = 0

        # process steps
        for hds_id, hds in self.input_datasets.items():
            job = self.creating_jobs[hds.id]
            index = len(wf["steps"])
            input_name = self.input_dataset_labels[hds_id]
            input_description = ""
            p_top += v_step
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

        # reset top position
        p_top = p_top - (v_step * (len(self.input_datasets) / 2))

        # process intermediate and final steps
        for job_id, job in self.processing_jobs.items():

            # update top position
            p_left += h_step

            # compute the step index
            index = len(wf["steps"])

            # get the tool related to the current job
            tool = self._get_tool(job.wrapped["tool_id"])

            # log
            print "Processing {0} node: {1}".format(job_id, tool.name)

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
                params[job_input_name] = _json.dumps({"__class__": "RuntimeValue"})
                inputs.append({
                    "description": "Runtime input value {0}".format(job_input_name),
                    "name": job_input_name
                })
                output_name = self.intermediate_dataset_labels[job_input_info["id"]] \
                    if job_input_info["id"] in self.intermediate_dataset_labels else "output"
                input_connections[job_input_name] = {
                    "id": self._input_order_map[job_input_info["id"]],
                    "output_name": output_name
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

        # save workflow
        if filename is not None:
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
