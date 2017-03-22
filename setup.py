import os
import shutil
import ConfigParser
import subprocess as _subprocess
from setuptools import setup
from distutils.command.clean import clean
from setuptools.command.build_py import build_py


def update_properties(config):
    repo_url = _subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).strip("\n")
    branch = _subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip("\n")
    tags = _subprocess.check_output(['git', 'show-ref', '--tags', '-s']).strip("\n")
    last_commit = _subprocess.check_output(['git', 'log', '--format=%H', '-n', '1']).strip("\n")

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

    # docker tag
    if last_commit in tags:
        tag = _subprocess.check_output(['git', 'describe', '--contains', last_commit]).strip("\n")
        docker_tag = "alpine-{0}".format(tag)
    else:
        docker_tag = "alpine-{0}".format(branch)

    # Git repository info
    config.add_section("Repository")
    config.set("Repository", "url", repo_url)
    config.set("Repository", "branch", branch)
    config.set("Repository", "owner", owner)
    config.set("Repository", "repo", repo)
    config.set("Repository", "last commit", last_commit)

    # Docker info
    config.add_section("Docker")
    config.set("Docker", "repository", owner)
    config.set("Docker", "tag", docker_tag)


class BuildCommand(build_py):
    """Custom build command."""

    def run(self):
        config = ConfigParser.ConfigParser()
        update_properties(config)

        with open("wft4galaxy/wft4galaxy.properties", "wb") as fp:
            config.write(fp)
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
        'bioblend': ['bioblend>=0.8.0'],
        'ruamel.yaml': ['ruamel.yaml'],  # TODO: to be removed in the next release
        'lxml': ['lxml'],
        'pyyaml': ['pyyaml'],
        'sphinx_rtd_theme': ['sphinx_rtd_theme'],
        'Jinja2': ['Jinja2>=2.9'],
        'docker': ['docker>=2.1.0'],
        'dockerpty': ['dockerpty>=0.4.1']
    },
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
