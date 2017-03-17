from __future__ import print_function

import os as _os
import sys as _sys
from future.utils import iteritems as _iteritems
from ruamel.yaml import round_trip_dump as _round_trip_dump
from ruamel.yaml.comments import CommentedMap as _CommentedMap
from json import load as _json_load
from json import dumps as _json_dumps

# BioBlend dependecies
from bioblend.galaxy.tools import ToolClient as _ToolClient

# wft4galaxy dependencies
import wft4galaxy.common as _common

# set logger
_logger = _common._logger

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
            print("'{0}': {1}".format(step_id, ", ".join([x["label"] for x in step_outputs.values()])), file=stream)

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


def get_workflow_info(filename, tools_folder=DEFAULT_TOOLS_FOLDER, galaxy_url=None, galaxy_api_key=None):
    definition, inputs, params, expected_outputs = _get_workflow_info(filename=filename,
                                                                      tool_folder=tools_folder,
                                                                      galaxy_url=galaxy_url,
                                                                      galaxy_api_key=galaxy_api_key)
    return Workflow(definition, inputs, params, expected_outputs)


def _get_workflow_info(filename, galaxy_url, galaxy_api_key, tool_folder=DEFAULT_TOOLS_FOLDER):
    inputs = []
    params = _CommentedMap()
    outputs = {}

    # setup galaxy instance
    galaxy_instance = _common._get_galaxy_instance(galaxy_url, galaxy_api_key)
    galaxy_tool_client = _ToolClient(galaxy_instance.gi)  # get the non-object version of the GI

    if not _os.path.exists(DEFAULT_TOOLS_FOLDER):
        _os.makedirs(DEFAULT_TOOLS_FOLDER)

    with open(filename) as fp:
        wf_config = _json_load(fp)

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
            tool = galaxy_instance.tools.get(tool_id)
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
            tool_params.insert(len(tool_params), input_el.get("name"), "", comment=input_el.get("label"))
        elif input_el_type in ["integer", "float", "color"]:
            tool_params.insert(len(tool_params), input_el.get("name"), input_el.get("value"),
                               comment=input_el.get("label"))
        elif input_el_type in ["data_column"]:
            tool_params.insert(len(tool_params), input_el.get("name"), input_el.get("default_value"),
                               comment=input_el.get("label"))
        elif input_el_type == "boolean":
            input_el_value = input_el.get("truevalue", "true") \
                if input_el.get("checked") else input_el.get("falsevalue", "false")
            tool_params.insert(len(tool_params), input_el.get("name"), input_el_value, comment=input_el.get("label"))
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
