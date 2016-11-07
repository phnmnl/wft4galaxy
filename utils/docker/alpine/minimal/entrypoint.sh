#!/usr/bin/env bash

source set-bioblend-env.sh "$@"

ENTRYPOINT=$1
if [[ ! ${ENTRYPOINT} =~ ^(bash|wft4galaxy)$  ]]; then
  ENTRYPOINT="wft4galaxy"
fi

if [[ ${ENTRYPOINT} == "bash" ]]; then
    /bin/bash ${WFT4GALAXY_OPTS}
else
    wft4galaxy ${WFT4GALAXY_OPTS}
fi
