import os
import shutil
from setuptools import setup
import subprocess as _subprocess
from json import dump as _json_dump
from distutils.command.clean import clean
from setuptools.command.build_py import build_py


def _run_cmd(cmd):
    if hasattr(_subprocess, "run"):
        return _subprocess.run(cmd, stdout=_subprocess.PIPE).stdout.decode("utf-8").strip("\n")
    else:
        return _subprocess.check_output(cmd).strip("\n")


def update_properties(config):
    repo_url = _run_cmd(['git', 'config', '--get', 'remote.origin.url'])
    branch = _run_cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    last_commit = _run_cmd(['git', 'log', '--format=%H', '-n', '1'])

    # get tags
    tags = []
    try:
        # Git repository could not contain tags
        # and the following command fails in such a case.
        # We simply ignore this failure
        tags = _run_cmd(['git', 'show-ref', '--tags', '-s'])
    except:
        pass

    # extract Git repository info
    if repo_url.startswith("git@"):
        # ssh protocol
        info = repo_url.split(":")
        owner_repo = info[1].split("/")
        owner = owner_repo[0].strip()
        repo = owner_repo[1].strip("\n.git")
    elif repo_url.startswith("https://"):
        # https protocol
        info = repo_url.split("https://")
        owner_repo = info[1].split("/")
        owner = owner_repo[1].strip()
        repo = owner_repo[2].strip("\n.git")
    else:
        raise ValueError("Unknown Git repository scheme")

    # map the git phnmnl repository to the Crs4 DockerHub repository
    if owner == "phnmnl":
        owner = "crs4"

    # git & docker tag
    tag = None
    if last_commit in tags:
        tag = _run_cmd(['git', 'describe', '--contains', last_commit])
        docker_tag = "alpine-{0}".format(tag)
    else:
        docker_tag = "alpine-{0}".format(branch)

    # Git repository info
    config["Repository"] = {
        "url": repo_url,
        "branch": branch,
        "owner": owner,
        "repo": repo,
        "last commit": last_commit,
        "tag": tag
    }

    # Docker info
    config["Docker"] = {
        "repository": owner,
        "tag": docker_tag
    }


class BuildCommand(build_py):
    """Custom build command."""

    def run(self):
        config = dict()
        update_properties(config)

        with open("wft4galaxy/wft4galaxy.properties", "w") as fp:
            _json_dump(config, fp, indent=4)
        build_py.run(self)


class CleanCommand(clean):
    def _rmrf(self, path):
        """
        Remove a file or directory.         
        """
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError:
            pass

    def run(self):
        clean.run(self)
        garbage_list = [
            "DEFAULT_HADOOP_HOME",
            "build",
            "dist",
            "wft4galaxy.egg-info",
            "wft4galaxy/wft4galaxy.properties",
            "results"
        ]
        for p in garbage_list:
            self._rmrf(p)


setup(
    name='wft4galaxy',
    description='Utility module for testing Galaxy workflows',
    url='https://github.com/phnmnl/wft4galaxy',
    version='0.1',
    install_requires={
        'setuptools': ['setuptools'],
        'future': ['future>=0.16.0'],
        'bioblend': ['bioblend'],
        'ruamel.yaml': ['ruamel.yaml'],  # TODO: to be removed in the next release
        'lxml': ['lxml'],
        'pyyaml': ['pyyaml'],
        'sphinx_rtd_theme': ['sphinx_rtd_theme'],
        'Jinja2': ['Jinja2>=2.9'],
        'docker': ['docker>=2.1.0'],
        'dockerpty': ['dockerpty>=0.4.1']
    },
    dependency_links=['git+https://github.com/galaxyproject/bioblend.git/@master#egg=bioblend-latest'],
    package_data={'wft4galaxy': ['wft4galaxy.properties'], 'templates': ['*']},
    packages=["wft4galaxy", "wft4galaxy.comparators", "wft4galaxy.app", "templates"],
    entry_points={'console_scripts': [
        'wft4galaxy = wft4galaxy.app.runner:main',
        'wft4galaxy-wizard = wft4galaxy.app.wizard:main',
        'wft4galaxy-docker = wft4galaxy.app.docker_runner:main'
    ]},
    cmdclass={
        "build_py": BuildCommand,
        "clean": CleanCommand
    },
)
