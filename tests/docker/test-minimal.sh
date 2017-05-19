#!/usr/bin/env bash

# FIXME: check path
IMAGE_ROOT_PATH=${1:-"utils/docker/minimal"}

# download wft4galaxy script
curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/install.sh | bash /dev/stdin .

# switch the Docker image context
cd ${IMAGE_ROOT_PATH}

# build docker image
./build-remote.sh && cd -

# Run examples  # FIXME: change the repo and version TAGs
wft4galaxy-docker --repository kikkomep --version minimal-travis-integration \
                  --server ${GALAXY_URL} --api-key ${GALAXY_CONFIG_MASTER_API_KEY} \
                  -f examples/change_case/workflow-test.yml