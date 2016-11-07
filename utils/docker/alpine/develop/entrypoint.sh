#!/usr/bin/env bash

source set-bioblend-env.sh "$@"

if [[ ${1} == "wft4galaxy" ]]; then
    shift
    wft4galaxy "$@"
elif [[ ${1} == "ipython" ]]; then
		ipython ${WFT4GALAXY_OPTS}
elif [[ ${1} == "jupyter" ]]; then
		ipython notebook --ip=$(hostname) --no-browser --port 8888 ${WFT4GALAXY_OPTS}
elif [[ ${1} == "bash" ]]; then
    /bin/bash ${WFT4GALAXY_OPTS}
else
	  /bin/bash ${WFT4GALAXY_OPTS}
fi
