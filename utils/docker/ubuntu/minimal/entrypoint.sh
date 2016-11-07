#!/usr/bin/env bash

source set-bioblend-env.sh "$@"

if [[ ${1} == "bash" ]]; then
    /bin/bash ${WFT4GALAXY_OPTS}
else
    wft4galaxy "$@"
fi
