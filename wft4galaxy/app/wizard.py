from __future__ import print_function

import os as _os
import sys as _sys
import jinja2 as _jinja2
import logging as _logging
import argparse as _argparse
import datetime as _datetime

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
_logger = _common.LoggerManager.get_logger(__name__)


# fix an issue related to the output buffering
# when the wizard is running within a Docker container
def disable_output_buffering():
    if _sys.version_info[0] == 2:
        _logger.debug("Disabling output buffering...")
        _sys.stdout = _os.fdopen(_sys.stdout.fileno(), 'w', 0)


def write_test_suite_definition_file(output_file, suite_config):
    j2_env = _jinja2.Environment(loader=_jinja2.FileSystemLoader(_TEMPLATE_DIR), trim_blocks=True)
    try:
        file_content = j2_env.get_template('workflow-test-template.yaml').render(config=suite_config)
        _logger.debug("Workflow test definition file:%s\n\n%s", output_file, file_content)
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
        ds_filename = _os.path.join(output_folder,
                                    "{0}.{1}".format(labels[ds.id], ds.file_ext) if labels is not None else ds.name)
        _logger.debug("Downloading dataset \"%s\" from \"%s\" ...", ds.id, ds.wrapped["url"])
        with open(ds_filename, "wb") as ds_in_fp:
            ds.download(ds_in_fp)
        _logger.debug("Dataset \"%s\" downloaded to \"%s\: done", ds.id, ds_filename)


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
    _logger.info("Writing workflow test definition file to %s ...", output_filename)
    write_test_suite_definition_file(output_filename, suite)
    _logger.debug("Writing workflow test definition file to %s: done", output_filename)
    _logger.info("Test definition template folder correctly generated.\n ===> See folder: %s", output_folder)


def generate_test_case(config):
    # instantiate the history wrapper
    hw = _wrapper.History(config["history-id"],
                          galaxy_url=config["galaxy_url"], galaxy_api_key=config["galaxy_api_key"])

    # set the output folder
    output_folder = _os.path.abspath(config["output_folder"])

    # make directory structure of the test definition
    make_dir_structure(output_folder)

    # extract workflow
    workflow_definition_filename = _os.path.join(output_folder, DEFAULT_WORFLOW_DEFINITION_FILENAME)
    wf_def = hw.extract_workflow(workflow_definition_filename)

    # download input datasets
    _logger.info("Downloading input datasets...")
    download_dataset(hw.input_datasets.values(), _os.path.join(output_folder, DEFAULT_INPUTS_FOLDER))
    _logger.info("Downloading input datasets: done")

    # download output datasets
    _logger.info("Downloading output datasets...")
    download_dataset(hw.output_datasets.values(), _os.path.join(output_folder, DEFAULT_EXPECTED_FOLDER),
                     labels=hw.output_dataset_labels)
    _logger.info("Downloading output datasets: done")

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
                                                 "{0}.{1}".format(hw.output_dataset_labels[ds.id], ds.file_ext)))

    # append test case to the test suite
    suite.add_workflow_test(cfg)

    # write the definition file
    _logger.info("Saving workflow test definition ...")
    wf_test_file = _os.path.join(output_folder, config["file"])
    write_test_suite_definition_file(wf_test_file, suite)
    _logger.debug("Workflow test definition saved to %s", wf_test_file)
    _logger.info("Saving workflow test definition: done")


def _get_history_info(config):
    result = None
    gi = _common.get_galaxy_instance(config["galaxy_url"], config["galaxy_api_key"])
    _logger.info("Loading Galaxy history info ...")
    candidate_histories = [h for h in gi.histories.list() if config["history"] in h.name]
    candidate_count = len(candidate_histories)
    if candidate_count == 0:
        print("\n No history found with name: \"{0}\"".format(config["history"]))
    elif candidate_count == 1:
        result = candidate_histories[0]
    else:
        while True:
            print("\nNOTICE:".ljust(10),
                  "More than one history matches the name \"{0}\".".format(config["history"]))
            print("".ljust(9), "Please select one of the following options:\n")

            for opt, h in enumerate(candidate_histories):
                print("".ljust(3), "{0})".format(opt + 1).ljust(4), h.name.ljust(30),
                      "".ljust(4), "create-time:",
                      _datetime.datetime.strptime(h.wrapped["create_time"], "%Y-%m-%dT%H:%M:%S.%f").strftime(
                          "%Y-%m-%d %H:%M:%S"))
            print("\n".ljust(4), "0)".ljust(4), "Exit")

            try:
                # get the user choice as int
                # notice that `input` in python3 is equivalent to `raw_input` in python2
                choice = int(input("\n ==> Choice: "))
                if choice in range(0, candidate_count + 1):
                    if choice > 0:
                        result = candidate_histories[choice - 1]
                        print("\n")
                    break
            except ValueError:
                print("\nWARNING: ".ljust(10), "Your choice is not valid!!!")
            except NameError:
                print("\nWARNING: ".ljust(10), "Your choice is not valid!!!")
            except SyntaxError:
                print("\nWARNING: ".ljust(10), "Your choice is not valid!!!")
            except KeyboardInterrupt:
                break
            else:
                print("\nWARNING: ".ljust(10), "Your choice is not valid!!!")
    return result


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
    test_parser.add_argument('history', help='History name')

    template_parser = command_subparsers_factory.add_parser(_TEMPLATE_CMD,
                                                            help="Generate a test definition template",
                                                            epilog=epilog)
    return main_parser


def main(args=None):
    # set args
    args = args if args else _sys.argv[1:]
    try:
        # disable output buffering
        disable_output_buffering()

        # process CLI args and opts
        parser = _make_parser()
        options = parser.parse_args(args)
        config = _common.Configuration(vars(options))

        # setup logging
        _common.LoggerManager.configure_logging(
            level=_logging.DEBUG if options.enable_debug else _logging.INFO,
            show_logger_name=True if options.enable_debug else False)

        # log the configuration
        _logger.debug("CLI config %r", config)
        # update defaults
        _common.configure_env_galaxy_server_instance(config, options)
        # log the configuration
        if options.enable_debug:
            _logger.debug("Configuration...")
            print(_common.pformat(config))
        if options.command == _TEMPLATE_CMD:
            generate_template(config)
        elif options.command == _TEST_CMD:
            history = _get_history_info(config)
            if history is not None:
                _logger.info("Selected history: %s (id: %r)", history.name, history.id)
                config["history-id"] = history.id
                generate_test_case(config)
    except Exception as e:
        _logger.error(e)
        if _logger.isEnabledFor(_logging.DEBUG):
            _logger.exception(e)


if __name__ == '__main__':
    main()
