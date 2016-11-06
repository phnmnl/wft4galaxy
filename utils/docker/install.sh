#!/bin/bash

# set the target script
TARGET_SCRIPT="/usr/local/bin/wft4galaxy-docker"

# set version
VERSION=${1:-wft4galaxy}
if [[ (${VERSION} != "wft4galaxy-dev:alpine") && (${VERSION} == "wft4galaxy-dev:ubuntu") ]]; then
	VERSION="wft4galaxy"
fi

# set the proper Docker image
curl -s https://bitbucket.org/kikkomep/workflowtester/raw/2f135c777ccc9a20c52fdd7da97d4708a36db2f8/utils/docker/wft4galaxy-docker.sh \
	| sudo sed "s/DOCKER_IMAGE=\"wft4galaxy\"/DOCKER_IMAGE='${VERSION}'/g" > ${TARGET_SCRIPT} \
	&& sudo chmod +x ${TARGET_SCRIPT}
