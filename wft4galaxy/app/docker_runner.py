#!/usr/bin/env python
from __future__ import print_function

import os as _os
import sys as _sys
import json as _json
import logging as _logging
import argparse as _argparse
import traceback as _traceback
import subprocess as _subprocess

# configure logger
_logger = _logging.getLogger("WorkflowTest")
_logger.setLevel(_logging.INFO)
_logFormatter = _logging.Formatter("%(asctime)s [wft4galaxy-docker] [%(levelname)-5.5s]  %(message)s")
_consoleHandler = _logging.StreamHandler()
_consoleHandler.setFormatter(_logFormatter)
_logger.addHandler(_consoleHandler)

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

# try to load wft4galaxy.properties
_properties = None
try:
    import wft4galaxy as _wft4galaxy

    with open(_os.path.join(_os.path.dirname(_wft4galaxy.__file__), "wft4galaxy.properties")) as fp:
        _properties = _json.load(fp)
        _logger.debug("wft4galaxy.properties: %r", _properties)
except:
    _logger.debug("No wft4galaxy.properties found! Use default settings!")

# Docker image settings
DOCKER_IMAGE_SETTINGS = {
    "registry": None,
    "repository": _properties["Docker"]["repository"] \
        if _properties is not None and "Docker" in _properties and "repository" in _properties["Docker"] else "crs4",
    "tag": _properties["Docker"]["tag"] \
        if _properties is not None and "Docker" in _properties and "tag" in _properties["Docker"] else "develop",
    "production": "wft4galaxy-minimal",
    "develop": "wft4galaxy-develop"
}

# Docker container settings
DOCKER_CONTAINER_SETTINGS = {
    "modes": ("production", "develop"),
    "entrypoints": {
        "runtest": ("runtest", 'Execute the wft4galaxy tool as entrypoint', DOCKER_IMAGE_SETTINGS["production"]),
        "bash": ("bash", 'Execute the BASH shell as entrypoint', DOCKER_IMAGE_SETTINGS["develop"]),
        "ipython": ("ipython", 'Execute the ipython as entrypoint', DOCKER_IMAGE_SETTINGS["develop"]),
        "jupyter": ("jupyter", 'Execute the jupyter as entrypoint', DOCKER_IMAGE_SETTINGS["develop"])
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


class _CommandLineHelper:
    def __init__(self):
        self._parser, self._entrypoint_parsers = self.setup()

    def setup(self):
        main_parser = _argparse.ArgumentParser(add_help=True)
        main_parser.add_argument('--registry', help='Alternative Docker registry', default=None)
        main_parser.add_argument('--repository', default=None,
                                 help='Alternative Docker repository containing the "wft4galaxy" Docker image')
        main_parser.add_argument('--image', help='Alternative "wft4galaxy" Docker image <NAME:TAG>', default=None)
        main_parser.add_argument('--local', action="store_true", default=False,
                                 help='Force to use the local version of the required Docker image')
        main_parser.add_argument('--server', help='Galaxy server URL', default=_os.environ["GALAXY_URL"])
        main_parser.add_argument('--api-key', help='Galaxy server API KEY', default=_os.environ["GALAXY_API_KEY"])
        main_parser.add_argument('-p', '--port', help='Docker port to expose', action="append", default=[])
        main_parser.add_argument('-v', '--volume', help='Docker volume to mount', type=str, action="append", default=[])
        main_parser.add_argument('--enable-logger', help='Enable log messages', action='store_true')
        main_parser.add_argument('--debug', help='Enable debug mode', action='store_true')

        # reference to the global options
        epilog = "NOTICE: Type \"{0} -h\" to see the global options.".format(main_parser.prog)

        # add entrypoint subparsers
        entrypoint_parsers = {}
        entrypoint_subparsers_factory = \
            main_parser.add_subparsers(title="Container entrypoint",
                                       description="entrypoint", dest="entrypoint",
                                       help="Available entrypoints of the Docker container")
        for ep_name, ep_help, ep_image in DOCKER_CONTAINER_SETTINGS["entrypoints"].values():
            entrypoint_parsers[ep_name] = \
                entrypoint_subparsers_factory.add_parser(ep_name, help=ep_help, epilog=epilog)

        # add wft4galaxy options
        wft4g_parser = entrypoint_parsers["runtest"]
        wft4g_parser.add_argument("-f", "--file",
                                  default=DEFAULT_CONFIG_FILENAME,
                                  help="YAML configuration file of workflow tests (default is \"{0}\")"
                                  .format(DEFAULT_CONFIG_FILENAME))
        wft4g_parser.add_argument("-o", "--output", metavar="output",
                                  default=DEFAULT_OUTPUT_FOLDER,
                                  help="Absolute path of the output folder (default is \"{0}\")"
                                  .format(DEFAULT_OUTPUT_FOLDER))
        wft4g_parser.add_argument('--disable-cleanup', help='Disable cleanup', action='store_true')
        wft4g_parser.add_argument('--disable-assertions', help='Disable assertions', action='store_true')
        wft4g_parser.add_argument("test", help="Workflow Test Name", nargs="*")

        # add bash options
        entrypoint_parsers["bash"].add_argument("cmd", nargs="*", help="BASH commands")

        # add jupyter options
        entrypoint_parsers["jupyter"].add_argument("--web-port", default=DEFAULT_JUPYTER_PORT, type=int,
                                                   help="Jupyter port (default is {0})".format(DEFAULT_JUPYTER_PORT))

        return main_parser, entrypoint_parsers

    def parse_args(self):
        args = self._parser.parse_args()
        # add port Jupyter web port
        if "web_port" in args:
            args.port.append("8888:{0}".format(args.web_port))
        _logger.debug("Parsed arguments %r", args)
        return args

    def print_usage(self):
        self._parser.print_usage()

    def print_help(self):
        self._parser.print_help()


class ContainerRunner:
    @staticmethod
    def run(options):
        if options.entrypoint == "runtest":
            return NonInteractiveContainer().run(options)
        else:
            return InteractiveContainer().run(options)


class Container():
    def get_image_name(self, options, pull_latest=True):
        img_name_parts = []
        # base default config
        config = DOCKER_CONTAINER_SETTINGS["entrypoints"][options.entrypoint]
        # set registry
        if options.registry is not None:
            img_name_parts.append(options.registry)
        elif DOCKER_IMAGE_SETTINGS["registry"]:
            img_name_parts.append(DOCKER_IMAGE_SETTINGS["registry"])
        # set repository
        if options.repository:
            img_name_parts.append(options.repository)
        else:
            img_name_parts.append(DOCKER_IMAGE_SETTINGS["repository"])
        # set image name
        if options.image:
            img_name_parts.append(options.image)
        else:
            img_name_parts.append("{0}:{1}".format(config[2], DOCKER_IMAGE_SETTINGS["tag"]))
        docker_image_name = "/".join(img_name_parts)
        _logger.debug("Using Docker image: %s", docker_image_name)

        if pull_latest:
            _logger.info("Updating Docker imge '{0}'".format(docker_image_name))
            p = _subprocess.Popen(["docker", "pull", docker_image_name], shell=False, close_fds=True,
                                  stdin=_subprocess.PIPE, stdout=_subprocess.PIPE)
            try:
                for o in p.stdout:
                    if isinstance(o, bytes):
                        o = o.decode("utf-8")
                    _logger.info("{0}".format(o).rstrip())
            except Exception as e:
                if options and options.debug:
                    _logger.exception(e)
        else:
            _logger.info("Using the local version of the Docker image '{0}'".format(docker_image_name))

        return docker_image_name


class InteractiveContainer(Container):
    def _parse_volumes(self, volumes):
        result = {}
        if volumes:
            for v_str in volumes:
                v_info = v_str.split(":")
                if len(v_info) != 2:
                    raise ValueError(
                        "Invalid volume parameter '{0}'. See 'docker run' syntax for more details.".format(v_str))
                result[v_info[0]] = {"bind": v_info[1]}
        return result

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
            docker_image = self.get_image_name(options, not options.local)

            # volumes
            volumes = self._parse_volumes(options.volume)

            # ports
            ports = self._parse_ports(options.port)

            # environment
            environment = ["GALAXY_URL={0}".format(_os.environ["GALAXY_URL"]),
                           "GALAXY_API_KEY={0}".format(_os.environ["GALAXY_API_KEY"])]

            # command
            command = [
                options.entrypoint,
                "--server", _os.environ["GALAXY_URL"],
                "--api-key", _os.environ["GALAXY_API_KEY"]
            ]

            # create and run Docker containers
            client = _docker.APIClient()
            container = client.create_container(
                image=docker_image,
                stdin_open=True,
                tty=True,
                command=command,
                environment=environment,
                volumes=volumes,
                ports=list(ports.keys()),
                host_config=client.create_host_config(port_bindings=ports)
            )
            _logger.info("Started Docker container %s", container["Id"])
            _dockerpty.start(client, container)
            client.remove_container(container["Id"])
            _logger.info("Removed Docker container %s", container["Id"])
            return _SUCCESS_EXIT
        except NameError:
            print("\n ERROR: To use wft4galaxy-docker in development mode "
                  "you need to install 'docker' and 'dockerpty' Python libries \n"
                  "\tType \"pip install docker dockerpty\" to install the required libraries.")
            if options and options.debug:
                _traceback.print_exc()
            return _FAILURE_EXIT
        except Exception as e:
            print("\n ERROR: Unable to start the Docker container: {0}".format(str(e)))
            if options and options.debug:
                _traceback.print_exc()
            return _FAILURE_EXIT


class NonInteractiveContainer(Container):
    def run(self, options):
        """

        :param options: 
        :return: 
        """
        ## extract folder of the configuration file
        options.volume.append(_os.path.abspath(_os.path.dirname(options.file)) + ":/data_input")
        options.volume.append(_os.path.abspath(_os.path.dirname(options.output)) + ":/data_output")

        # prepare the Docker image (updating it if required)
        docker_image = self.get_image_name(options, not options.local)

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
        # Galaxy environment variables
        cmd.extend(["-e", "GALAXY_URL={0}".format(options.server or _os.environ["GALAXY_URL"])])
        cmd.extend(["-e", "GALAXY_API_KEY={0}".format(options.api_key or _os.environ["GALAXY_API_KEY"])])
        # image
        cmd.append(docker_image)
        # entrypoint
        # TODO: update the entrypoint of the Docker container
        cmd.append("wft4galaxy")
        # log debug option
        if options.debug:
            cmd.append("--debug")
        # Galaxy settings server (redundant)
        cmd += ["--server ", options.server]  # or _os.environ["GALAXY_URL"]]
        cmd += ["--api-key ", options.api_key]  # or _os.environ["GALAXY_API_KEY"]]
        # configuration file
        cmd += ["-f", "/data_input/" + _os.path.basename(options.file)]
        # output folder
        cmd += ["-o", options.output]
        # cleanup option
        if options.disable_cleanup:
            cmd.append("--disable-cleanup")
        # assertion option
        if options.disable_assertions:
            cmd.append("--disable-assertions")

        # add test filter
        cmd += options.test

        # output the Docker command (just for debugging)
        _logger.debug("Command parts: %r", cmd)
        _logger.debug("Command string: %s", ' '.join(cmd))
        #########################################################

        # launch the Docker container
        p = _subprocess.Popen(cmd, shell=False, close_fds=False,
                              stdin=_subprocess.PIPE, stdout=_subprocess.PIPE)
        # write Docker output
        try:
            for o in p.stdout:
                if isinstance(o, bytes):
                    o = o.decode("utf-8")
                _sys.stdout.write(o)
        except Exception as e:
            if options and options.debug:
                _logger.exception(e)

        # wait for termination and report the exit code
        return p.wait()


def _logger_setup(options):
    # add file logs
    log_file = None
    if log_file:
        fileHandler = _logging.FileHandler(log_file)
        fileHandler.setFormatter(_logFormatter)
        _logger.addHandler(fileHandler)
    if options.debug:
        _logger.setLevel(_logging.DEBUG)
    _logger.debug("Command line options %r", options)


def main():
    options = None
    try:
        # parse cli options/arguments
        p = _CommandLineHelper()
        options = p.parse_args()

        # update logger
        _logger_setup(options)

        # log Python version
        _logger.debug("Python version: %s", _sys.version)

        # run container
        ctr = ContainerRunner()
        exit_code = ctr.run(options)
        _logger.debug("Docker container terminated with %d exit code", exit_code)

        # report the Docker container exit code
        _sys.exit(exit_code)

    except Exception as e:
        print("\nERROR: {0}".format(str(e)))
        if options and options.debug:
            _traceback.print_exc()
        _sys.exit(_FAILURE_EXIT)


if __name__ == '__main__':
    main()
