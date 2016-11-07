#!/bin/bash

# set the target script
BASE_SCRIPT="https://bitbucket.org/kikkomep/workflowtester/raw/docker-tools/utils/docker/wft4galaxy-docker.sh"
#BASE_SCRIPT="https://raw.githubusercontent.com/phnmnl/wft4galaxy/docker-tools/utils/docker/wft4galaxy-docker.sh"
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
