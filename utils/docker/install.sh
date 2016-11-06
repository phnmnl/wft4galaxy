#!/bin/bash

# set the target script
BASE_SCRIPT="https://bitbucket.org/kikkomep/workflowtester/raw/docker-tools/utils/docker/wft4galaxy-docker.sh"
#BASE_SCRIPT="https://raw.githubusercontent.com/phnmnl/wft4galaxy/docker-tools/utils/docker/wft4galaxy-docker.sh"
TARGET_SCRIPT="/usr/local/bin/wft4galaxy-docker"

# set version
VERSION=${1:-wft4galaxy}
if [[ (${VERSION} != "wft4galaxy-dev:alpine") && (${VERSION} == "wft4galaxy-dev:ubuntu") ]]; then
	VERSION="wft4galaxy"
fi

# set the proper Docker image
curl -s ${BASE_SCRIPT} \
	| sudo sed "s/DOCKER_IMAGE=\"wft4galaxy\"/DOCKER_IMAGE='${VERSION}'/g" > ${TARGET_SCRIPT} \
	&& sudo chmod +x ${TARGET_SCRIPT}
