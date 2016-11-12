#!/bin/bash

# set the target script
BASE_SCRIPT="https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/wft4galaxy-docker"
TARGET_SCRIPT="/usr/local/bin/wft4galaxy-docker"

# set base os
BASE_OS=${1:-alpine}
if [[ ! ${BASE_OS} =~ ^(alpine|ubuntu)$ ]]; then
	echo -e "\n Invalid OS '${BASE_OS}'"
	exit
fi

# set the proper Docker image
curl -s ${BASE_SCRIPT} \
	| sudo sed "s/BASE_OS=\"alpine\"/BASE_OS='${BASE_OS}'/g" > ${TARGET_SCRIPT} \
	&& sudo chmod +x ${TARGET_SCRIPT}
