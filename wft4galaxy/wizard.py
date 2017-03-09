from __future__ import print_function
from future.utils import iteritems as _iteritems
from past.builtins import basestring as _basestring

import os as _os
import sys as _sys
import json as _json
import jinja2 as _jinja2
import logging as _logging
import argparse as _argparse

from wft4galaxy import core as _wft4core
from wft4galaxy.common import Configuration
from wft4galaxy.common import TestConfigError
from wft4galaxy.common import ENV_KEY_GALAXY_URL
from wft4galaxy.common import ENV_KEY_GALAXY_API_KEY
from wft4galaxy.common import make_dirs as _makedirs
from wft4galaxy.common import _set_galaxy_server_settings
from wft4galaxy.common import _pformat

# default output settings
DEFAULT_OUTPUT_FOLDER = "test-config"
DEFAULT_INPUTS_FOLDER = "inputs"
DEFAULT_EXPECTED_FOLDER = "expected"
DEFAULT_TEST_DEFINITION_FILENAME = "workflow-test-suite.yml"

# command string
_OPTION_CMD = "command"
_TEST_CMD = "generate-test"
_TEMPLATE_CMD = "generate-template"

# templates directory
_TEMPLATE_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), _os.pardir, "templates")
print(_TEMPLATE_DIR)

# configure module logger
LogFormat = '%(asctime)s %(levelname)s: %(message)s'
_logging.basicConfig(format=LogFormat)
_logger = _logging.getLogger("WorkflowTest")
_logger.setLevel(_logging.INFO)


def write_test_suite_definition_file(output_file, suite_config):
    j2_env = _jinja2.Environment(loader=_jinja2.FileSystemLoader(_TEMPLATE_DIR), trim_blocks=True)
    try:
        file_content = j2_env.get_template('workflow-test-template.yaml').render(config=suite_config)
        _logger.debug("==>Output file:\n%s", file_content)
        with open(output_file, "w") as out:
            out.write(file_content)
    except _jinja2.exceptions.UndefinedError as e:
        print(e.message)


if __name__ == '__main__':
    main()
