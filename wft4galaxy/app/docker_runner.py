#!/usr/bin/env python
from __future__ import print_function

import re as _re
import os as _os
import sys as _sys
import json as _json
import logging as _logging
import argparse as _argparse
import subprocess as _subprocess

# configure logger
_log_format = "%(asctime)s [wft4galaxy-docker] [%(levelname)-5.5s]  %(message)s"
_logger = _logging.getLogger("WorkflowTest-Docker")
_logger_handler = _logging.StreamHandler()
_logger_formatter = _logging.Formatter(_log_format)
_logger_handler.setFormatter(_logger_formatter)
_logger.addHandler(_logger_handler)

# try to load modules required for running container interactively
try:
    import docker as _docker
    import dockerpty as _dockerpty
except ImportError:
    _logger.debug("Packages 'docker' and 'dockerpty' are not available")

# Exit codes
_SUCCESS_EXIT = 0
_FAILURE_EXIT = -1

# Jupyter port
DEFAULT_JUPYTER_PORT = 9876

# absolute path of this script
_script_path = _os.path.realpath(__file__)
_logger.debug("Script path: %s" % _script_path)

# try to load wft4galaxy.properties if the script belongs to an installed instance of wft4galaxy
_properties = None
try:
    _properties_file_path = _os.path.abspath(_os.path.join(_script_path, _os.pardir, _os.pardir))
    with open(_os.path.join(_properties_file_path, "wft4galaxy.properties")) as fp:
        _properties = _json.load(fp)
        _logger.debug("wft4galaxy.properties: %r", _properties)
except:
    _logger.debug("No wft4galaxy.properties found! Use default settings!")

# Docker image settings
DOCKER_IMAGE_SETTINGS = {
    "registry": None,
    "owner": "crs4",
    "production": "wft4galaxy",
    "develop": "wft4galaxy-develop",
    "default_tag_version": "latest",
    "repository": _properties["Docker"]["repository"] \
        if _properties is not None and "Docker" in _properties and "repository" in _properties["Docker"] else "crs4"
}

# Docker container settings
DOCKER_CONTAINER_SETTINGS = {
    "modes": ("production", "develop"),
    "entrypoints": {
        "runtest": ("runtest", 'Execute the "wft4galaxy" tool as entrypoint', DOCKER_IMAGE_SETTINGS["production"]),
        "generate-template": ("wizard", 'Execute the "generate-template" wizard '
                                        'command as entrypoint', DOCKER_IMAGE_SETTINGS["production"]),
        "generate-test": ("wizard", 'Execute the "generate-test" wizard '
                                    'command as entrypoint', DOCKER_IMAGE_SETTINGS["production"]),
        "bash": ("bash", 'Execute the "Bash" shell as entrypoint', DOCKER_IMAGE_SETTINGS["develop"]),
        "ipython": ("ipython", 'Execute the "Ipython" shell as entrypoint', DOCKER_IMAGE_SETTINGS["develop"]),
        "jupyter": ("jupyter", 'Execute the "Jupyter" server as entrypoint', DOCKER_IMAGE_SETTINGS["develop"])
    }
}
# WorkflowTest configuration defaults
DEFAULT_HISTORY_NAME_PREFIX = "_WorkflowTestHistory_"
DEFAULT_WORKFLOW_NAME_PREFIX = "_WorkflowTest_"
DEFAULT_OUTPUT_FOLDER = "results"
DEFAULT_CONFIG_FILENAME = "workflow-test-suite.yml"
DEFAULT_WORKFLOW_CONFIG = {
    "file": "workflow.ga",
    "output_folder": DEFAULT_OUTPUT_FOLDER,
    "inputs": {
        "Input Dataset": {"name": "Input Dataset", "file": ["input"]}
    },
    "expected": {
        "output1": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output1"},
        "output2": {"file": "expected_output", "comparator": "filecmp.cmp", "name": "output2"}
    }
}


class _CustomFormatter(_argparse.RawTextHelpFormatter):
    """ Customize settings of the default RawTextHelpFormatter """

    def __init__(self, prog, indent_increment=2, max_help_position=40, width=None):
        super(_CustomFormatter, self).__init__(prog, indent_increment, max_help_position, width)


class _CommandLineHelper:
    def __init__(self, omit_subparsers=False):
        self._parser, self._entrypoint_parsers = self.setup(omit_subparsers)

    def setup(self, omit_subparsers=False):

        main_parser = _argparse.ArgumentParser(add_help=True, formatter_class=_argparse.RawTextHelpFormatter)
        main_parser.add_argument('--repository', default=None, metavar="REPO", dest="repository",
                                 help='Alternative Docker image repository of '
                                      'the "wft4galaxy" Docker image (default is "crs4/wft4galaxy[-develop]")')
        main_parser.add_argument('--tag', default=None, metavar="VERSION_TAG",
                                 help='Alternative version tag of the "wft4galaxy" Docker image '
                                      '(default is "{}")'.format(DOCKER_IMAGE_SETTINGS["default_tag_version"]))
        main_parser.add_argument('--skip-update', action="store_true", default=False,
                                 help='Skip the update of the "wft4galaxy" Docker image '
                                      'and use the local version if it is available')
        main_parser.add_argument('--server', help='Galaxy server URL', default=None)
        main_parser.add_argument('--api-key', help='Galaxy server API KEY', default=None)
        main_parser.add_argument('--port', help='Docker port to expose', action="append", default=[])
        main_parser.add_argument('--volume', help='Docker volume to mount', type=str, action="append", default=[])
        main_parser.add_argument('--network', help='Docker network to join', default=None)
        main_parser.add_argument('--debug', help='Enable debug mode', action='store_true')

        # reference to the global options
        epilog = "NOTICE: Type \"{0} -h\" to see the global options.".format("wft4galaxy-docker")

        # add entrypoint subparsers
        entrypoint_parsers = None
        if omit_subparsers:
            main_parser.add_argument('--entrypoint', help='Absolute path of a log file.', default="runtest")
        else:
            entrypoint_parsers = {}
            entrypoint_subparsers_factory = \
                main_parser.add_subparsers(title="Container entrypoint", dest="entrypoint",
                                           description="Available entrypoints for the 'wft4galaxy' Docker image.",
                                           help="Choose one of the following options:")
            for ep_name in DOCKER_CONTAINER_SETTINGS["entrypoints"].keys():
                ep_cmd, ep_help, ep_image = DOCKER_CONTAINER_SETTINGS["entrypoints"][ep_name]
                entrypoint_parsers[ep_name] = \
                    entrypoint_subparsers_factory.add_parser(ep_name, help=ep_help, epilog=epilog)

            # add bash options
            entrypoint_parsers["bash"].add_argument("cmd", nargs="*", help="BASH commands")

            # add jupyter options
            entrypoint_parsers["jupyter"].add_argument("--web-port", default=DEFAULT_JUPYTER_PORT, type=int,
                                                       help="Jupyter port (default is {0})".format(
                                                           DEFAULT_JUPYTER_PORT))

            # add generate-test options
            entrypoint_parsers["generate-test"].add_argument("history", help="History name")
            entrypoint_parsers["generate-test"].add_argument(
                "-o", "--output", dest="output", default="test-config",
                help="absolute path of the output folder (default is \"test-config\")")
            entrypoint_parsers["generate-test"].add_argument(
                "-f", "--file", default="workflow-test-suite.yml",
                help="YAML configuration file of workflow tests (default is\"workflow-test-suite.yml\"")

            # add generate-test options
            entrypoint_parsers["generate-template"].add_argument(
                "-o", "--output", dest="output", default="test-config",
                help="absolute path of the output folder (default is \"test-config\")")
            entrypoint_parsers["generate-template"].add_argument(
                "-f", "--file", default="workflow-test-suite.yml",
                help="YAML configuration file of workflow tests (default is\"workflow-test-suite.yml\"")

        # add wft4galaxy options to a subparser or directly to the main_parser
        wft4g_parser = main_parser if omit_subparsers else entrypoint_parsers["runtest"]
        wft4g_parser.add_argument("-f", "--file",
                                  default=DEFAULT_CONFIG_FILENAME,
                                  help="YAML configuration file of workflow tests (default is \"{0}\")"
                                  .format(DEFAULT_CONFIG_FILENAME))
        wft4g_parser.add_argument("-o", "--output", metavar="PATH",
                                  default=DEFAULT_OUTPUT_FOLDER,
                                  help="Absolute path of the output folder (default is \"{0}\")"
                                  .format(DEFAULT_OUTPUT_FOLDER))
        wft4g_parser.add_argument('--enable-logger', help='Enable log messages', action='store_true')
        wft4g_parser.add_argument('--disable-cleanup', help='Disable cleanup', action='store_true')

        # here we hardcode the possible values of wft4galaxy.core.OutputFormat because we don't
        # want to require installing the package to use the docker runner.
        wft4g_parser.add_argument('--output-format', choices=('text', 'xunit'), help='Choose output type',
                                  default='text')
        wft4g_parser.add_argument('--xunit-file', default=None, metavar="PATH",
                                  help='Set the path of the xUnit report file (absolute or relative to the output folder)')
        wft4g_parser.add_argument("test", help="Workflow Test Name", nargs="*")

        return main_parser, entrypoint_parsers

    def parse_args(self):
        args = self._parser.parse_args()
        # add port Jupyter web port
        if "web_port" in args:
            args.port.append("{0}:{1}".format(args.web_port, args.web_port))
        _logger.debug("Parsed arguments %r", args)
        return args

    def print_usage(self):
        self._parser.print_usage()

    def print_help(self):
        self._parser.print_help()


class ContainerRunner:
    @staticmethod
    def run(options):
        if options.entrypoint in ("runtest", "generate-test", "generate-template"):
            return NonInteractiveContainer().run(options)
        else:
            return InteractiveContainer().run(options)


class Container():
    def get_image_name(self, options, skip_update=False):

        # base default config
        config = DOCKER_CONTAINER_SETTINGS["entrypoints"][options.entrypoint]

        image_repository = None
        if options.repository is not None:
            image_repository = options.repository

        else:
            #
            img_name_parts = []

            # set registry
            if _properties and "registry" in _properties["Docker"]:
                img_name_parts.append(_properties["Docker"]["registry"])
            elif DOCKER_IMAGE_SETTINGS["registry"]:  # set default registry if exists
                img_name_parts.append(DOCKER_IMAGE_SETTINGS["registry"])
            # set repository
            if _properties and "owner" in _properties["Docker"]:
                img_name_parts.append(_properties["Docker"]["owner"])
            elif DOCKER_IMAGE_SETTINGS["owner"]:  # set default registry if exists
                img_name_parts.append(DOCKER_IMAGE_SETTINGS["owner"])
            # set image name
            img_name_parts.append(config[2])

            # build the fully qualified Docker image name
            image_repository = "/".join(img_name_parts)
            _logger.debug("Using Docker image: %s", image_repository)

        # try to use the version tag provided by user
        image_tag = DOCKER_IMAGE_SETTINGS["default_tag_version"]
        if options.tag is not None:
            image_tag = options.tag
        # if the user doesn't provide a version
        else:
            # if wft4galaxy has installed, try to use its metadata
            if _properties is not None and "Repository" in _properties:
                # if the installed version has tag, use it
                image_tag = _properties["Repository"]["tag"] if "tag" in _properties["Repository"] else None
                # if the installed version has not a tag, use the branch of the Git repository as version
                if image_tag is None \
                        and _properties["Repository"]["branch"] and "branch" in _properties["Repository"]:
                    image_tag = _properties["Repository"]["branch"]

        # replace not valid forward, backward slashes and other not valid characters with dashes
        image_tag = _re.sub('[\\\\/:*?"<>|]', '-', image_tag)

        # build the fully qualified image name
        docker_image_fqn = "{0}:{1}".format(image_repository, image_tag)

        # if the user doesn't disable this option,
        # try to pull the last version the required image
        if not skip_update:
            _logger.info("Updating Docker imge '{0}'".format(docker_image_fqn))
            p = _subprocess.Popen(["docker", "pull", docker_image_fqn], shell=False, close_fds=False)
            try:
                p.communicate()
            except KeyboardInterrupt:
                print("\n")
                _logger.warn("Pull of Docker image %s interrupted by user", docker_image_fqn)
        else:
            _logger.info("Using the local version of the Docker image '{0}'".format(docker_image_fqn))

        return docker_image_fqn


class InteractiveContainer(Container):
    def _parse_volumes(self, volumes):
        mounts = []
        result = {}
        if volumes:
            for v_str in volumes:
                v_info = v_str.split(":")
                if len(v_info) != 2:
                    raise ValueError(
                        "Invalid volume parameter '{0}'. See 'docker run' syntax for more details.".format(v_str))
                if not _os.path.isabs(v_info[0]):
                    v_info[0] = _os.path.abspath(v_info[0])
                result[v_info[0]] = {"bind": v_info[1], "mode": "rw"}
                mounts.append(v_info[1])
        return mounts, result

    def _parse_ports(self, ports):
        result = {}
        if ports:
            for p_str in ports:
                p_info = p_str.split(":")
                if len(p_info) == 1:
                    result[p_info[0]] = None
                elif len(p_info) == 2:
                    result[p_info[0]] = p_info[1]
                else:
                    raise ValueError(
                        "Invalid port parameter '{0}'. See 'docker run' syntax for more details.".format(p_str))
        return result

    def run(self, options):
        """

        :param options:
        :return:
        """
        if options.entrypoint == "runtest":
            raise ValueError("You cannot use the entrypoint 'runtest' in interactive mode!")
        try:

            # prepare the Docker image (updating it if required)
            docker_image = self.get_image_name(options, options.skip_update)

            # volumes
            vmounts, volumes = self._parse_volumes(options.volume)

            # ports
            ports = self._parse_ports(options.port)

            # environment
            environment = ["GALAXY_URL={0}".format(options.server),
                           "GALAXY_API_KEY={0}".format(options.api_key)]

            # command
            command = [
                options.entrypoint,
                "--server", options.server,
                "--api-key", options.api_key
            ]
            if "web_port" in options:
                command.extend(["--port", "{}".format(options.web_port)])
            import socket
            # create and run Docker containers
            client = _docker.APIClient()
            container = client.create_container(
                image=docker_image,
                stdin_open=True,
                tty=True,
                hostname=socket.gethostname(),
                command=command,
                environment=environment,
                volumes=vmounts,
                ports=list(ports.keys()),
                host_config=client.create_host_config(binds=volumes, port_bindings=ports)
            )
            _logger.info("Started Docker container %s", container["Id"])
            _dockerpty.start(client, container)
            client.remove_container(container["Id"])
            _logger.info("Removed Docker container %s", container["Id"])
            return _SUCCESS_EXIT
        except NameError as ne:
            if options and options.debug:
                _logger.exception(ne)
            print("\n ERROR: To use wft4galaxy-docker in development mode "
                  "you need to install 'docker' and 'dockerpty' Python libries \n"
                  "\tType \"pip install docker dockerpty\" to install the required libraries.\n")
            return _FAILURE_EXIT
        except Exception as e:
            _logger.error("ERROR: Unable to start the Docker container: {0}".format(str(e)))
            if options and options.debug:
                _logger.exception(e)
            return _FAILURE_EXIT


class NonInteractiveContainer(Container):
    def run(self, options):
        """

        :param options:
        :return:
        """
        # set absolute path of container mount points for IO
        container_input_path = _os.path.join("/", "data_input")
        container_output_path = _os.path.join("/", "data_output")

        # extract folder of the configuration file
        options.volume.append("{0}:{1}".format(
            _os.path.abspath(_os.path.dirname(options.file)), container_input_path))
        options.volume.append("{0}:{1}".format(
            _os.path.abspath(_os.path.dirname(options.output)), container_output_path))

        # prepare the Docker image (updating it if required)
        docker_image = self.get_image_name(options, options.skip_update)

        ########################################################
        # build docker cmd
        ########################################################
        # main command
        cmd = ['docker', 'run', '-i', '--rm']
        # add Docker volumes
        for v in options.volume:
            cmd += ["-v", v]
        # add Docker ports
        for p in options.port:
            cmd += ["-p", p]
        # attach container to a specific Docker network
        if options.network:
            cmd.extend(["--network", options.network])

        # Galaxy environment variables
        cmd.extend(["-e", "GALAXY_URL={0}".format(options.server)])
        cmd.extend(["-e", "GALAXY_API_KEY={0}".format(options.api_key)])
        # image
        cmd.append(docker_image)
        # entrypoint
        cmd.append(DOCKER_CONTAINER_SETTINGS["entrypoints"][options.entrypoint][0])
        # log debug option
        if options.debug:
            cmd.append("--debug")
        # Galaxy settings server (redundant)
        cmd += ["--server", options.server]
        cmd += ["--api-key", options.api_key]
        # configuration file
        cmd += ["-f",
                options.file if options.entrypoint in ("generate-test", "generate-template")
                else _os.path.join(container_input_path, _os.path.basename(options.file))]
        # output folder
        cmd += ["-o", _os.path.join(container_output_path, options.output)]

        # wft4galaxy entrypoint specific options
        if options.entrypoint in ("wft4galaxy", "runtest"):
            # enable logger option
            if options.enable_logger:
                cmd.append("--enable-logger")
            # cleanup option
            if options.disable_cleanup:
                cmd.append("--disable-cleanup")
            # output format options
            cmd.extend(('--output-format', options.output_format))
            if options.xunit_file:
                cmd.extend(("--xunit-file", options.xunit_file))
            # add test filter
            cmd += options.test

        # append "wizard" subcommand
        if options.entrypoint in ("generate-test", "generate-template"):
            cmd.append(options.entrypoint)

        # 'generate-test' entrypoint specific options
        if options.entrypoint == "generate-test":
            cmd.append(options.history)

        # output the Docker command (just for debugging)
        _logger.debug("Command parts: %r", cmd)
        _logger.debug("Command string: %s", ' '.join(cmd))
        #########################################################

        # launch the Docker container
        p = _subprocess.Popen(cmd, close_fds=False)
        try:
            p.communicate()
            # wait for termination and report the exit code
            return p.wait()
        except KeyboardInterrupt:
            p.kill()
            _logger.warn("wft4galaxy terminated by user")
            return _FAILURE_EXIT


def _set_galaxy_env(options):
    ENV_KEY_GALAXY_URL = "GALAXY_URL"
    if options.server is None:
        if ENV_KEY_GALAXY_URL in _os.environ:
            options.server = _os.environ[ENV_KEY_GALAXY_URL]
        else:
            raise ValueError("Galaxy URL not defined! "
                             "Use --server or the environment variable {}.\n".format(ENV_KEY_GALAXY_URL))
    ENV_KEY_GALAXY_API_KEY = "GALAXY_API_KEY"
    if options.api_key is None:
        if ENV_KEY_GALAXY_API_KEY in _os.environ:
            options.api_key = _os.environ[ENV_KEY_GALAXY_API_KEY]
        else:
            raise ValueError("Galaxy API key not defined! "
                             "Use --api-key or the environment variable {}.\n".format(ENV_KEY_GALAXY_API_KEY))


def main():
    options = None
    try:
        # arguments set
        args = set(_sys.argv[1:])

        # check if we need to print help
        print_help = len(args & set(["-h", "--help"])) != 0

        # check at list one entrypoint is specified
        # if not, it is assumed to be "runtest"
        omit_subparsers = len(args & set(DOCKER_CONTAINER_SETTINGS["entrypoints"])) == 0 and not print_help

        # initialize the CLI helper
        p = _CommandLineHelper(omit_subparsers=omit_subparsers)

        # print help and exit
        if print_help and omit_subparsers:
            p.print_help()
            _sys.exit(_SUCCESS_EXIT)

        # parse cli options/arguments
        options = p.parse_args()

        # update logger
        if options.debug:
            _logger.setLevel(_logging.DEBUG)

        # print CLI options
        _logger.debug("Command line options %r", options)

        # set galaxy_env
        _set_galaxy_env(options)

        # log Python version
        _logger.debug("Python version: %s", _sys.version)

        # run container
        ctr = ContainerRunner()
        exit_code = ctr.run(options)
        _logger.debug("Docker container terminated with %d exit code", exit_code)

        # report the Docker container exit code
        _sys.exit(exit_code)

    except Exception as e:
        _logger.error("ERROR: {0}".format(str(e)))
        if options and options.debug:
            _logger.exception(e)
        _sys.exit(_FAILURE_EXIT)


if __name__ == '__main__':
    main()
