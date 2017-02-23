from setuptools import setup

setup(
    name='wft4galaxy',
    description='Utility module for testing Galaxy workflows',
    url='https://github.com/phnmnl/wft4galaxy',
    version='0.1',
    install_requires={
        'setuptools': ['setuptools'],
        'bioblend': ['bioblend>=0.8.0'],
        'ruamel.yaml': ['ruamel.yaml'],
        'lxml': ['lxml'],
        'pyyaml': ['pyyaml'],
        'sphinx_rtd_theme': ['sphinx_rtd_theme']
    },
    packages=["wft4galaxy", "wft4galaxy.comparators"],
    scripts=['utils/docker/wft4galaxy-docker'],
    entry_points={'console_scripts': ['wft4galaxy = wft4galaxy.core:run_tests']},
)
