from __future__ import print_function

import os as _os
import sys as _sys
import jinja2 as _jinja2
import logging as _logging
import argparse as _argparse

# wft4galaxy dependencies
import wft4galaxy.core as _core
import wft4galaxy.common as _common
import wft4galaxy.wrapper as _wrapper

# default output settings
DEFAULT_OUTPUT_FOLDER = "test-config"
DEFAULT_INPUTS_FOLDER = "inputs"
DEFAULT_EXPECTED_FOLDER = "expected"
DEFAULT_WORFLOW_DEFINITION_FILENAME = "workflow.ga"
DEFAULT_TEST_DEFINITION_FILENAME = "workflow-test-suite.yml"

# command string
_OPTION_CMD = "command"
_TEST_CMD = "generate-test"
_TEMPLATE_CMD = "generate-template"

# templates directory
_TEMPLATE_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), _os.pardir, _os.pardir, "templates")

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


def make_dir_structure(output_folder):
    # make directory structure of the test definition
    _common.makedirs(output_folder)
    _common.makedirs(_os.path.join(output_folder, DEFAULT_INPUTS_FOLDER))
    _common.makedirs(_os.path.join(output_folder, DEFAULT_EXPECTED_FOLDER))


def download_dataset(datasets, output_folder, labels=None):
    for ds in datasets:
        ds_in_filename = _os.path.join(output_folder,
                                       "{0}.{1}".format(labels[ds.id], ds.file_ext) if labels is not None else ds.name)
        with open(ds_in_filename, "w") as ds_in_fp:
            ds.download(ds_in_fp)


def generate_template(config):
    _logger.info("Generating test definition template folder...")
    # config a sample suite
    suite = _core.WorkflowTestSuite(config["galaxy_url"], config["galaxy_api_key"])
    cfg = _core.WorkflowTestCase(name="workflow_test_case_1")
    cfg.output_folder = config["output_folder"]
    cfg.enable_debug = config["enable_debug"]
    cfg.add_input("input_1", "{0}/<INPUT_FILE_PATH>".format(DEFAULT_INPUTS_FOLDER), "txt")
    cfg.add_expected_output("output_1", "{0}/<OUTPUT_FILE_PATH>".format(DEFAULT_EXPECTED_FOLDER))
    suite.add_workflow_test(cfg)
    output_folder = _os.path.abspath(config["output_folder"])
    output_filename = _os.path.join(output_folder, config["file"])
    # make directory structure of the test definition
    make_dir_structure(output_folder)
    # write the definition file
    write_test_suite_definition_file(output_filename, suite)
    _logger.info("Test definition template folder correctly generated.\n ===> See folder: %s", output_folder)


def generate_test_case(config):
    gi = _common._get_galaxy_instance(config["galaxy_url"], config["galaxy_api_key"])

    # get history object
    h = gi.histories.get(config["history-name"])

    # instantiate the history wrapper
    hw = _wrapper.HistoryWrapper(h)

    # set the output folder
    output_folder = _os.path.abspath(config["output_folder"])

    # make directory structure of the test definition
    make_dir_structure(output_folder)

    # extract workflow
    workflow_definition_filename = _os.path.join(output_folder, DEFAULT_WORFLOW_DEFINITION_FILENAME)
    wf_def = hw.extract_workflow(workflow_definition_filename)

    # download input datasets
    download_dataset(hw.input_datasets.values(), _os.path.join(output_folder, DEFAULT_INPUTS_FOLDER))

    # download output datasets
    download_dataset(hw.output_datasets.values(), _os.path.join(output_folder, DEFAULT_EXPECTED_FOLDER),
                     labels=hw.output_dataset_labels)

    # load the wf wrapper
    wf = _wrapper.Workflow.load(workflow_definition_filename)

    suite = _core.WorkflowTestSuite(config["galaxy_url"], config["galaxy_api_key"])
    cfg = _core.WorkflowTestCase(name="workflow_test_case_1")
    cfg.output_folder = _core.WorkflowTestCase.DEFAULT_OUTPUT_FOLDER
    cfg.enable_debug = config["enable_debug"]

    # configure input
    for ds in hw.input_datasets.values():
        cfg.add_input(hw.input_dataset_labels[ds.id],
                      "{0}/{1}".format(DEFAULT_INPUTS_FOLDER, ds.wrapped["name"]), ds.file_ext)

    # configure output
    for ds in hw.output_datasets.values():
        cfg.add_expected_output(hw.output_dataset_labels[ds.id],
                                "{0}/{1}".format(DEFAULT_EXPECTED_FOLDER,
                                                 "{0}.{1}".format(hw.output_dataset_labels[ds.id], ds.file_ext)),
                                "comparators.csv_same_row_and_col_lengths")

    # append test case to the test suite
    suite.add_workflow_test(cfg)

    # write the definition file
    write_test_suite_definition_file(_os.path.join(output_folder, config["file"]), suite)


def _make_parser():
    main_parser = _argparse.ArgumentParser()
    # log settings
    main_parser.add_argument('--debug', help='Enable debug mode', action='store_true', default=False,
                             dest="enable_debug")
    # Galaxy instance settings
    main_parser.add_argument('--server', help='Galaxy server URL (default $GALAXY_URL)', dest="galaxy_url")
    main_parser.add_argument('--api-key', help='Galaxy server API KEY (default $GALAXY_API_KEY)', dest="galaxy_api_key")
    # output settings
    main_parser.add_argument('-o', '--output', dest="output_folder", default=DEFAULT_OUTPUT_FOLDER,
                             help='absolute path of the output folder (default is "{0}")'.format(DEFAULT_OUTPUT_FOLDER))
    main_parser.add_argument("-f", "--file", default=DEFAULT_TEST_DEFINITION_FILENAME,
                             help="YAML configuration file of workflow tests (default is \"{0}\")"
                             .format(DEFAULT_TEST_DEFINITION_FILENAME))
    # reference to the global options
    epilog = "NOTICE: Type \"{0} -h\" to see the global options.".format(main_parser.prog)

    # add entrypoint subparsers
    command_subparsers_factory = \
        main_parser.add_subparsers(title="command",
                                   description="command", dest=_OPTION_CMD,
                                   help="Wizard tool command: [generate-test | generate-template]")

    # add wizard options
    test_parser = command_subparsers_factory.add_parser(_TEST_CMD,
                                                        help="Generate a test definition file from a history",
                                                        epilog=epilog)

    # test_parser.add_argument('workflow-name', help='Workflow name')
    test_parser.add_argument('history-name', help='History name')

    template_parser = command_subparsers_factory.add_parser(_TEMPLATE_CMD,
                                                            help="Generate a test definition template",
                                                            epilog=epilog)
    return main_parser


def main(args=None):
    # default configuration of the logger
    # _logging.basicConfig(format=LogFormat)

    # set args
    args = args if args else _sys.argv[1:]
    try:
        # process CLI args and opts
        parser = _make_parser()
        options = parser.parse_args(args)
        config = _common.Configuration(vars(options))

        # enable debug mode
        if options.enable_debug:
            _logger.setLevel(_logging.DEBUG)
        # log the configuration
        _logger.debug("CLI config %r", config)
        # update defaults
        _common._set_galaxy_server_settings(config, options)
        # log the configuration
        _logger.info("Configuration...")
        print(_common._pformat(config))
        if options.command == _TEMPLATE_CMD:
            generate_template(config)
        elif options.command == _TEST_CMD:
            generate_test_case(config)
    except Exception as e:
        _logger.error(e)
        if _logger.isEnabledFor(_logging.DEBUG):
            _logger.exception(e)


if __name__ == '__main__':
    main()
