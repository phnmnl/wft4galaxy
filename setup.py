from setuptools import setup

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
    package_data={'templates': ['*']},
    packages=["wft4galaxy", "wft4galaxy.comparators", "wft4galaxy.app", "templates"],
    scripts=['utils/docker/wft4galaxy-docker'],
    entry_points={'console_scripts': [
        'wft4galaxy = wft4galaxy.app.runner:main',
        'wft4galaxy-wizard = wft4galaxy.app.wizard:main',
        'wft4galaxy-docker = wft4galaxy.utils.docker_runner:run'
    ]}
)
