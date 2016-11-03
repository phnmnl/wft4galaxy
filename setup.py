from setuptools import setup

setup(name='wft4galaxy',
      description='Utility package for testing Galaxy workflows',
      author='CRS4',
      url='https://bitbucket.org/crs4/wft4galaxy/',
      py_modules=['wft4galaxy'],
      entry_points={'console_scripts': ['wft4galaxy = wft4galaxy:run_tests']},
      )
