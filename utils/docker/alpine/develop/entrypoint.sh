#!/usr/bin/env bash

source set-bioblend-env.sh "$@"

ENTRYPOINT=$1
if [[ ! ${ENTRYPOINT} =~ ^(bash|wft4galaxy|runtest|ipython|jupyter)$  ]]; then
  ENTRYPOINT="bash"
fi

if [[ ${ENTRYPOINT} == "wft4galaxy" ]] || [[ ${ENTRYPOINT} == "runtest" ]]; then
    wft4galaxy ${WFT4GALAXY_OPTS}
elif [[ ${ENTRYPOINT} == "ipython" ]]; then
		ipython ${WFT4GALAXY_OPTS}
elif [[ ${ENTRYPOINT} == "jupyter" ]]; then
		ipython notebook --ip=$(hostname) --no-browser --port 8888 ${WFT4GALAXY_OPTS}
else
	  /bin/bash ${WFT4GALAXY_OPTS}
fi
