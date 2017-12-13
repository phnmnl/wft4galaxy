#!/usr/bin/env bash

source entrypoint-argparser.sh "$@"

if [[ ! "${ENTRYPOINT}" =~ ^(bash|wft4galaxy|runtest|wizard)$  ]]; then
    echo -e "\nERROR: Command \"${ENTRYPOINT_ARGS} \" not supported !"
    echo -e "       Supported commands: bash | wft4galaxy | runtest | wizard \n"
    exit 99
fi

if [[ "${ENTRYPOINT}" == "bash" ]]; then
    /bin/bash "${ENTRYPOINT_ARGS[@]}"
elif [[ "${ENTRYPOINT}" == "wizard" ]]; then
    wft4galaxy-wizard "${ENTRYPOINT_ARGS[@]}"
else
    wft4galaxy "${ENTRYPOINT_ARGS[@]}"
fi
