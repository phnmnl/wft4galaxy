from __future__ import print_function

import os as _os
import sys as _sys
import uuid as _uuid
import json as _json
import collections as _collections
from future.utils import iteritems as _iteritems

from bioblend import ConnectionError
from future.utils import iteritems as _iteritems
from ruamel.yaml import round_trip_dump as _round_trip_dump
from ruamel.yaml.comments import CommentedMap as _CommentedMap

# BioBlend dependecies
from bioblend.galaxy.tools import ToolClient as _ToolClient

# wft4galaxy dependencies
import wft4galaxy.common as _common

# set logger
from wft4galaxy.common import TestConfigError

_logger = _common.default_logger

# Default folder where tool configuration is downloaded
DEFAULT_TOOLS_FOLDER = ".tools"


class Workflow(object):
    """
    Display workflow information which are relevant to configure a workflow test.
    """

    def __init__(self, definition, inputs, params, outputs):
        self.definition = definition
        self.inputs = inputs
        self.params = params
        self.outputs = outputs

    def show_inputs(self, stream=_sys.stdout):
        """
        Print workflow inputs to file.
        """
        max_chars = max([len(x["name"]) for x in self.inputs])
        for i in self.inputs:
            print("- ", i["name"].ljust(max_chars),
                  ("  # " + i["description"] if len(i["description"]) > 0 else ""), file=stream)

    def show_params(self, stream=_sys.stdout):
        """
        Print parameters needed by workflow tools to file.
        """
        print(_round_trip_dump(self.params), file=stream)

    def show_outputs(self, stream=_sys.stdout):
        """
        Print workflow outputs (indexed by workflow step) to file.
        """
        for step_id, step_outputs in _iteritems(self.outputs):
            print(
                "'{0}': {1}".format(step_id, ", ".join([x["label"] for x in step_outputs.values()])),
                file=stream)

    @staticmethod
    def load(filename, galaxy_url=None, galaxy_api_key=None, tools_folder=DEFAULT_TOOLS_FOLDER):
        """
        Return the :class:`Workflow` instance related to the workflow defined in ``filename``

        :type filename: str
        :param filename: the path of the ``.ga`` workflow definition

        :type galaxy_url: str
        :param galaxy_url: url of your Galaxy server instance.

        :type galaxy_api_key: str
        :param galaxy_api_key: an API key from your Galaxy server instance.

        :type tools_folder: str
        :param tools_folder: optional temp folder where tool definitions are downloaded (``.tools`` by default)

        :rtype: :class:`Workflow`
        :return: the :class:`Workflow` instance related to the workflow defined in ``filename``
        """
        return get_workflow_info(filename=filename, tools_folder=tools_folder,
                                 galaxy_url=galaxy_url, galaxy_api_key=galaxy_api_key)


def get_workflow_info(filename, tools_folder=DEFAULT_TOOLS_FOLDER, galaxy_url=None,
                      galaxy_api_key=None):
    definition, inputs, params, expected_outputs = _get_workflow_info(filename=filename,
                                                                      tool_folder=tools_folder,
                                                                      galaxy_url=galaxy_url,
                                                                      galaxy_api_key=galaxy_api_key)
    return Workflow(definition, inputs, params, expected_outputs)


def _get_workflow_info(filename, galaxy_url, galaxy_api_key, tool_folder=DEFAULT_TOOLS_FOLDER):
    inputs = []
    params = _CommentedMap()
    outputs = {}

    # loading wf info start
    _logger.debug("Loading workflow definition from %s file...", filename)

    # setup galaxy instance
    galaxy_instance = _common.get_galaxy_instance(galaxy_url, galaxy_api_key)
    galaxy_tool_client = _ToolClient(galaxy_instance.gi)  # get the non-object version of the GI

    if not _os.path.exists(DEFAULT_TOOLS_FOLDER):
        _os.makedirs(DEFAULT_TOOLS_FOLDER)

    with open(filename) as fp:
        wf_config = _json.load(fp)

    for sid, step in _iteritems(wf_config["steps"]):
        # tool = gi.tools.get()

        _logger.debug("Processing step '%s' -- '%s'", sid, step["name"])

        # an input step....
        if not step["tool_id"] and step["type"] == "data_input":
            for input_ in step["inputs"]:
                _logger.debug("Processing input: '%s' (%s)", input_["name"], input_["description"])
                inputs.append(input_)

        # a processing step (with outputs) ...
        if step["tool_id"] and step["type"] == "tool":

            # tool parameters
            tool_params = _CommentedMap()

            # process tool info to extract parameters
            tool_id = step["tool_id"]
            # tool = galaxy_instance.tools.get(tool_id)
            ## LP:  re-write this using the bioblend.objects API to fetch the tool
            # inputs.  See the comment above `def _process_tool_param_element`
            # tool_config_xml = _os.path.basename(tool.wrapped["config_file"])
            # _logger.debug("Processing step tool '%s'", tool_id)
            #
            # try:
            #     _logger.debug("Download TOOL '%s' definition file XML: %s....", tool_id, tool_config_xml)
            #     targz_filename = _os.path.join(DEFAULT_TOOLS_FOLDER, tool_id + ".tar.gz")
            #     targz_content = galaxy_tool_client._get(_os.path.join(tool_id, "download"), json=False)
            #     if targz_content.status_code == 200:
            #         with open(targz_filename, "w") as tfp:
            #             tfp.write(targz_content.content)
            #         tar = _tarfile.open(targz_filename)
            #         tar.extractall(path=tool_folder)
            #         tar.close()
            #         _os.remove(targz_filename)
            #         _logger.debug("Download TOOL '%s' definition file XML: %s....: DONE", tool_id, tool_config_xml)
            #     else:
            #         _logger.debug("Download TOOL '%s' definition file XML: %s....: ERROR %r",
            #                       tool_id, tool_config_xml, targz_content.status_code)
            #
            #     tool_config_xml = _os.path.join(DEFAULT_TOOLS_FOLDER, tool_config_xml)
            #     if _os.path.exists(tool_config_xml):
            #         tree = _etree.parse(tool_config_xml)
            #         root = tree.getroot()
            #         inputs_el = root.find("inputs")
            #         for input_el in inputs_el:
            #             _process_tool_param_element(input_el, tool_params)
            #         if len(tool_params) > 0:
            #             params.insert(int(sid), sid, tool_params)
            #
            # except _StandardError as e:
            #     _logger.debug("Download TOOL '%s' definition file XML: %s....: ERROR", tool_id, tool_config_xml)
            #     _logger.error(e)

            # process
            outputs[str(sid)] = {}
            for output in step["workflow_outputs"]:
                outputs[str(sid)][output["uuid"]] = output

    # loading wf info end
    _logger.debug("Workflow definition loaded from %s file...", filename)

    # return loaded info
    return wf_config, inputs, params, outputs


# XXX:  TODO
# This can be replaced by using the object oriented bioblend API to fetch
# the tool inputs directly through the API.
#
# Try something like:
#   t = gi.tools.get("ChangeCase", io_details=True)
# The process t.wrapped['inputs'] to get this information.
#
def _process_tool_param_element(input_el, tool_params):
    """
        Parameter types:
             1) text                    X
             2) integer and float       X
             3) boolean                 X
             4) data                    X (no default option)
             5) select                  ~ (not with OPTIONS)
             6) data_column             X (uses the default_value attribute)
             7) data_collection         X (no default option)
             8) drill_down              X (no default option)
             9) color                   X

        Tag <OPTION> is allowed for the following types:
            1) select                   X

        Tag <OPTIONS> is allowed for the following types of PARAM:
            1) select
            2) data
          ... options can be extracted by :
            a) from_data_table
            b) from dataset
            c) from_file
            d) from_parameter
            e) filter

    :param input_el: an XML param element
    :param tool_params: a CommentMap instance
    :return:
    """
    input_el_type = input_el.get("type")
    if (input_el.tag == "param" or input_el.tag == "option") \
            and input_el.get("type") != "data":
        if input_el_type in ["text", "data", "data_collection", "drill_down"]:
            tool_params.insert(len(tool_params), input_el.get("name"), "",
                               comment=input_el.get("label"))
        elif input_el_type in ["integer", "float", "color"]:
            tool_params.insert(len(tool_params), input_el.get("name"), input_el.get("value"),
                               comment=input_el.get("label"))
        elif input_el_type in ["data_column"]:
            tool_params.insert(len(tool_params), input_el.get("name"),
                               input_el.get("default_value"),
                               comment=input_el.get("label"))
        elif input_el_type == "boolean":
            input_el_value = input_el.get("truevalue", "true") \
                if input_el.get("checked") else input_el.get("falsevalue", "false")
            tool_params.insert(len(tool_params), input_el.get("name"), input_el_value,
                               comment=input_el.get("label"))
        elif input_el_type == "select":
            selected_option_el = input_el.find("option[@selected]")

            selected_option_el = selected_option_el \
                if selected_option_el is not None \
                else input_el.getchildren()[0] if len(input_el.getchildren()) > 0 else None
            if selected_option_el is not None:
                tool_params.insert(len(tool_params), input_el.get("name"),
                                   selected_option_el.get("value"),
                                   comment=input_el.get("label"))
    elif input_el.tag == "conditional":
        conditional_options = _CommentedMap()
        for conditional_param in input_el.findall("param"):
            _process_tool_param_element(conditional_param, conditional_options)
        tool_params.insert(len(tool_params), input_el.get("name"),
                           conditional_options, comment=input_el.get("label"))
        for when_el in input_el.findall("when"):
            when_options = _CommentedMap()
            for when_option in when_el.findall("param"):
                _process_tool_param_element(when_option, when_options)
            if len(when_options) > 0:
                conditional_options.insert(len(conditional_options),
                                           when_el.get("value"),
                                           when_options)


class History(object):
    def __init__(self, history_id, galaxy_url=None, galaxy_api_key=None):
        super(History, self).__init__()

        # set the Galaxy instance
        self._gi = _common.get_galaxy_instance(galaxy_url, galaxy_api_key)

        # set wrapped history
        _logger.info("Loading history %s info", history_id)
        self._history = self._gi.histories.get(history_id)

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
        _logger.info("Processing history info...")
        self._process_history()
        _logger.info("History info processing: done")

    @property
    def jobs(self):
        return self._jobs

    def _get_job(self, job_id):
        if job_id not in self._jobs:
            try:
                _logger.debug("Loading job %s info...", job_id)
                self._jobs[job_id] = self._gi.jobs.get(job_id, full_details=True)
                _logger.debug("Loading job %s info: done", job_id)
            except ConnectionError as e:
                raise TestConfigError("Unable to retrieve job info !")
        return self._jobs[job_id]

    @property
    def tools(self):
        return self._tools

    def _get_tool(self, tool_id):
        if not tool_id in self._tools:
            try:
                _logger.debug("Loading tool %s info...", tool_id)
                self._tools[tool_id] = self._gi.tools.get(tool_id, io_details=True)
                _logger.debug("Loading tool %s info: done", tool_id)
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

            _logger.info("Processing dataset %s ... ", ds.id)

            # load job info
            creating_job = self._get_job(ds.wrapped["creating_job"])
            job_inputs = {in_info["id"]: in_name for in_name, in_info in
                          _iteritems(creating_job.wrapped["inputs"])}
            job_outputs = {out_info["id"]: out_name for out_name, out_info in
                           _iteritems(creating_job.wrapped["outputs"])}
            intermediate_datasets += list(job_inputs)

            # update auxiliary data info
            for in_id, in_name in _iteritems(job_inputs):
                if in_id not in ds_input_info:
                    ds_input_info[in_id] = {}
                ds_input_info[in_id][creating_job.id] = in_name

            for out_id, out_name in _iteritems(job_outputs):
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
                    self.job_input_ids[creating_job.id] = list(job_inputs)
                    self.job_output_ids[creating_job.id] = list(job_outputs)

            _logger.info("Process dataset %s: done ", ds.id)

        _logger.info("Processing extra info...")

        # Auxiliary function which computes the label for a given dataset
        def __set_label(labels, ds_id, info_matrix, label=None, prefix=None):
            if label is not None:
                labels[ds_id] = label
            elif ds_id in info_matrix and len(info_matrix[ds_id]) == 1:
                # use job
                labels[ds_id] = info_matrix[ds_id][list(info_matrix[ds_id])[0]]
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
                    __set_label(self.intermediate_dataset_labels, ds.id, ds_output_info,
                                prefix="output")
                else:
                    self.output_datasets[ds.id] = ds
                    __set_label(self.output_dataset_labels, ds.id, ds_output_info, prefix="output")

        intermediate_inputs = []
        not_ordered_inputs = list(self.input_datasets)
        input_datasets = _collections.OrderedDict()

        # determine the job level
        _logger.debug("Processing JOB levels ...")
        for job_id, job in _iteritems(self.processing_jobs):
            # compute and set the job level
            self.processing_job_levels[job_id] = self.compute_processing_job_level(job_id)
            # order inputs
            tool = self._get_tool(job.wrapped["tool_id"])
            ordered_names = [x["name"] for x in tool.wrapped["inputs"]]
            for name in ordered_names:
                if name in job.wrapped["inputs"]:
                    in_id = job.wrapped["inputs"][name]["id"]
                    if in_id in not_ordered_inputs:
                        input_datasets[in_id] = self.input_datasets[in_id]
                        not_ordered_inputs.remove(in_id)
            # add intermediate inputs
            intermediate_inputs.extend([x["id"] for x in job.wrapped["outputs"].values()
                                        if x["id"] not in self.output_datasets])
        _logger.debug("JOB levels processing: done")

        # copy remaining inputs
        for ds_in in not_ordered_inputs:
            input_datasets[ds_in] = self.input_datasets[ds_in]
        self.input_datasets = input_datasets
        inputs = list(self.input_datasets) + intermediate_inputs
        self._input_order_map = {x: inputs.index(x) for x in inputs}

        _logger.info("Processing extra info: done")

    def compute_processing_job_level(self, job_id):
        level = 0
        for job in self.processing_jobs.values():
            if job.id == job_id:
                break
            dependencies = [x for x in self.job_output_ids[job.id] if
                            x in self.job_input_ids[job_id]]
            if len(dependencies) > 0:
                level = max(level, self.processing_job_levels[job.id] + 1)
        return level

    def extract_workflow(self, filename=None, workflow_name=None, v_step=100, h_step=400):
        if workflow_name is None:
            workflow_name = "Workflow extracted from history {0}".format(self._history.id)

        # start
        _logger.info("Extracting Workflow from history...")

        # wf object representation
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
        for hds_id, hds in _iteritems(self.input_datasets):
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
        for job_id, job in _iteritems(self.processing_jobs):

            # update top position
            p_left += h_step

            # compute the step index
            index = len(wf["steps"])

            # get the tool related to the current job
            tool = self._get_tool(job.wrapped["tool_id"])

            # compute params
            params = {"__page__": 0, "__rerun_remap_job_id__": None}
            tool_inputs = {param["name"]: param for param in tool.wrapped["inputs"]}
            for param_name, param_info in _iteritems(job.wrapped["params"]):
                if param_name in tool_inputs:
                    params[param_name] = param_info

            # add inputs to tool state and inputs
            inputs = []
            input_connections = {}
            for job_input_name, job_input_info in _iteritems(job.wrapped["inputs"]):
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
            for job_output_name, job_output_info in _iteritems(job.wrapped["outputs"]):
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
                "content_id": tool.id,
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
                "tool_id": tool.id,
                "tool_state": _json.dumps(params),
                "tool_version": tool.version,
                "type": "tool",
                "uuid": str(_uuid.uuid1()),
                "workflow_outputs": workflow_outputs
            }

        # save workflow
        if filename is not None:
            _logger.info("Saving workflow to file...")
            with open(filename, "w") as fp:
                _logger.debug("Workflow file path: %s", filename)
                _json.dump(wf, fp, indent=4)
            _logger.info("Saving workflow to file: done")

        # extraction wf end
        _logger.info("Extracting Workflow from history: done")
        return wf
