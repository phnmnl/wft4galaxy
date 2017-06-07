#!/usr/bin/env bash

source entrypoint-argparser.sh "$@"

if [[ ! ${ENTRYPOINT} =~ ^(bash|ipython|jupyter|wft4galaxy|runtest|wizard)$ ]]; then
    echo -e "\nERROR: Command \"${ENTRYPOINT_ARGS} \" not supported !"
    echo -e "       Supported commands: bash | ipython| jupyter | wft4galaxy | runtest | wizard \n"
    exit 99
fi

if [[ ${ENTRYPOINT} == "wft4galaxy" ]] || [[ ${ENTRYPOINT} == "runtest" ]]; then
    wft4galaxy ${ENTRYPOINT_ARGS}
elif [[ ${ENTRYPOINT} == "wizard" ]]; then
    wft4galaxy-wizard ${ENTRYPOINT_ARGS}
elif [[ ${ENTRYPOINT} == "ipython" ]]; then
	ipython ${ENTRYPOINT_ARGS}
elif [[ ${ENTRYPOINT} == "jupyter" ]]; then
	ipython notebook --ip=$(hostname) --no-browser --allow-root ${ENTRYPOINT_ARGS}
else
    /bin/bash ${ENTRYPOINT_ARGS}
fi