# wft4galaxy: <br> Workflow Tester for Galaxy

Version: 0.1.0

## Description
**wft4galaxy** is a Python module which allows to automate the running of Galaxy workflow tests. It can be used either as local Python library or a Docker image running inside a Docker container.

## Installation

Basically, to install **wft4galaxy** as a local Python library, you need to follow the two speps below:

  1. clone the github repository:
  
      ```bash
      git clone https://github.com/phnmnl/wft4galaxy
      ```
      
  2. install the module using the usual setup script:
  
     ```bash
     cd wft4galaxy
     python setup.py install
     ```
     
> **Notice**. If you are using a Linux based system, like *Ubuntu*, you probably need to install the two libraries **`python-lxml`** and **`libyaml-dev`** as a further *prerequisite*.


Alternatively, you can use **wft4galaxy** with Docker (see [Docker-based Installation](http://wft4galaxy.readthedocs.io/installation.html#id2)).

## Usage Instructions

If you have installed **wft4galaxy** as native Python library, you can launch it from your terminal:

``` bash
wft4galaxy [options]
```

The the main available options are:

```bash
usage: wft4galaxy [-h] [--server GALAXY_URL] [--api-key GALAXY_API_KEY]
                  [-f FILE] [--enable-logger] [--debug] [--disable-cleanup]
                  [--output-format {text,xunit}] [--xunit-file FILE_PATH] [-o PATH]
                  [test [test ...]]

positional arguments:
  test                      Workflow Test Name

optional arguments:
  -h, --help                    show this help message and exit
  --server GALAXY_URL           Galaxy server URL
  --api-key GALAXY_API_KEY      Galaxy server API KEY
  -f FILE, --file FILE          YAML configuration file of workflow tests (default is workflow-test-suite.yml)
  --enable-logger               Enable log messages
  --debug                       Enable debug mode
  --disable-cleanup             Disable cleanup
  --output-format {text,xunit}  Choose output type
  --xunit-file FILE_PATH        Set the path of the xUnit report file (absolute or relative to the output folder)
  -o PATH, --output PATH        Path of the output folder
```

As an example, you can run tests defined in your ``workflow-test-suite.yml`` definition file by typing:

```bash
wft4galaxy
```

Alternatively, you can run one or more tests (e.g., ``change_case``) in your definition file specifying their names:

```bash
 wft4galaxy change_case
 ```

See [documentation](http://wft4galaxy.readthedocs.io/) for more details.
