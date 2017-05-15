from __future__ import print_function

import os as _os
import sys as _sys
import argparse as _argparse
import logging as _logging

import wft4galaxy.core as _core
import wft4galaxy.common as _common

# set logger
_logger = _common.LoggerManager.get_logger(__name__)


class _CustomFormatter(_argparse.RawTextHelpFormatter):
    """ Customize settings of the default RawTextHelpFormatter """

    def __init__(self, prog, indent_increment=2, max_help_position=40, width=None):
        super(_CustomFormatter, self).__init__(prog, indent_increment, max_help_position, width)


def _make_parser():
    parser = _argparse.ArgumentParser(add_help=True, formatter_class=_CustomFormatter)
    parser.add_argument("test", help="Workflow Test Name", nargs="*")
    parser.add_argument('--server', help='Galaxy server URL', dest="galaxy_url")
    parser.add_argument('--api-key', help='Galaxy server API KEY', dest="galaxy_api_key")
    parser.add_argument('-f', '--file', default=_core.WorkflowTestCase.DEFAULT_CONFIG_FILENAME,
                        help='YAML configuration file of workflow tests (default is {0})'.format(
                            _core.WorkflowTestCase.DEFAULT_CONFIG_FILENAME))
    parser.add_argument('--enable-logger', help='Enable log messages', action='store_true', default=None)
    parser.add_argument('--debug', help='Enable debug mode', action='store_true', default=None)
    parser.add_argument('--disable-cleanup', help='Disable cleanup', action='store_true', default=None)

    parser.add_argument('--xunit', help='Enable xUnit report', action='store_true', default=False)
    parser.add_argument('--xunit-file', default=None, metavar="FILE_PATH",
                        help='Set the path of the xUnit report file (absolute or relative to the output folder)')
    parser.add_argument('-o', '--output', dest="output_folder", metavar="PATH", help='Path of the output folder')
    return parser


def _parse_cli_arguments(parser, cmd_args):
    args = parser.parse_args(cmd_args)
    _logger.debug("Parsed arguments %r", args)

    if not _os.path.isfile(args.file):
        parser.error("Test file {} doesn't exist or isn't a file".format(args.file))
    if not _os.access(args.file, _os.R_OK):
        parser.error("Permission error.  Test file {} isn't accessible for reading".format(args.file))

    return args


def _configure_test(galaxy_url, galaxy_api_key, suite, output_folder, tests,
                    enable_logger, enable_debug, disable_cleanup, disable_assertions):
    # configure `galaxy_url`
    suite.galaxy_url = galaxy_url or suite.galaxy_url or _os.environ.get(_common.ENV_KEY_GALAXY_URL)
    if not suite.galaxy_url:
        raise _common.TestConfigError("Galaxy URL not defined!  Use --server or the environment variable {} "
                                      "or specify it in the test configuration".format(_common.ENV_KEY_GALAXY_URL))
    # configure `galaxy_api_key`
    suite.galaxy_api_key = galaxy_api_key \
                           or suite.galaxy_api_key \
                           or _os.environ.get(_common.ENV_KEY_GALAXY_API_KEY)
    if not suite.galaxy_api_key:
        raise _common.TestConfigError("Galaxy API key not defined!  Use --api-key or the environment variable {} "
                                      "or specify it in the test configuration".format(_common.ENV_KEY_GALAXY_API_KEY))
    # configure `output_folder`
    suite.output_folder = output_folder \
                          or suite.output_folder \
                          or _core.WorkflowTestCase.DEFAULT_OUTPUT_FOLDER

    if enable_logger is not None:
        suite.enable_logger = enable_logger

    if enable_debug is not None:
        suite.enable_debug = enable_debug

    if disable_cleanup is not None:
        suite.disable_cleanup = disable_cleanup

    if disable_assertions is not None:
        suite.disable_assertions = disable_assertions

    for test_config in suite.workflow_tests.values():
        test_config.disable_cleanup = suite.disable_cleanup
        test_config.disable_assertions = suite.disable_assertions

    # enable the logger with the proper detail level
    if suite.enable_logger or suite.enable_debug:
        _common.LoggerManager.update_log_level(_logging.DEBUG if suite.enable_debug else _logging.INFO)

    # log Python version
    _logger.debug("Python version: %s", _sys.version)

    # log the current configuration
    _logger.info("Configuration: %s", suite)


def run_tests(filename,
              galaxy_url=None, galaxy_api_key=None,
              enable_logger=None, enable_debug=None,
              disable_cleanup=None, disable_assertions=None,
              output_folder=None, enable_xunit=False, xunit_file=None, tests=None):
    """
    Run a workflow test suite defined in a configuration file.

    :type enable_logger: bool
    :param enable_logger: ``True`` to enable INFO messages; ``False`` (default) otherwise.

    :type enable_debug: bool
    :param enable_debug: ``True`` to enable DEBUG messages; ``False`` (default) otherwise.

    :type disable_cleanup: bool
    :param disable_cleanup: ``True`` to avoid the clean up of the workflow and history created on the Galaxy server;
        ``False`` (default) otherwise.

    :type disable_assertions: bool
    :param disable_assertions: ``True`` to disable assertions during the execution of the workflow test;
        ``False`` (default) otherwise.
    """

    # load suite configuration
    suite = _core.WorkflowTestSuite.load(filename,
                                         output_folder=output_folder)  # FIXME: do we need output_folder here ?
    _configure_test(galaxy_url=galaxy_url, galaxy_api_key=galaxy_api_key,
                    suite=suite, tests=tests, output_folder=output_folder,
                    enable_logger=enable_logger, enable_debug=enable_debug,
                    disable_cleanup=disable_cleanup, disable_assertions=disable_assertions)

    # run the configured test suite
    result = suite.run(galaxy_url=galaxy_url, galaxy_api_key=galaxy_api_key, verbosity=2,
                       enable_xunit=enable_xunit or (xunit_file != None), xunit_file=xunit_file,
                       enable_logger=enable_logger, enable_debug=enable_debug, disable_cleanup=disable_cleanup)
    # compute exit code
    exit_code = len([r for r in result.test_case_results if r.failed()])
    _logger.debug("wft4galaxy.run_tests exiting with code: %s", exit_code)
    return exit_code


def main():
    try:
        # parse arguments
        parser = _make_parser()
        options = _parse_cli_arguments(parser, _sys.argv[1:])

        # setup logging
        _common.LoggerManager.configure_logging(
            level=_logging.DEBUG if options.debug else _logging.INFO if options.enable_logger else _logging.ERROR,
            show_logger_name=True if options.debug else False
        )

        # run tests and collect exit code
        code = run_tests(filename=options.file,
                         galaxy_url=options.galaxy_url,
                         galaxy_api_key=options.galaxy_api_key,
                         output_folder=options.output_folder,
                         enable_logger=options.enable_logger,
                         enable_debug=options.debug,
                         disable_cleanup=options.disable_cleanup,
                         enable_xunit=options.xunit,
                         xunit_file=options.xunit_file,
                         tests=options.test)

        # report exit code to the system
        _sys.exit(code)
    except _common.RunnerStandardError as e:
        # in some cases we exit with an exception even for rather "normal"
        # situations, such as configuration errors.  For this reason we only display
        # the exception's stack trace if debug logging is enabled.
        _logger.error(e)
        if _logger.isEnabledFor(_logging.DEBUG):
            _logger.exception(e)
        _sys.exit(99)


if __name__ == '__main__':
    main()
