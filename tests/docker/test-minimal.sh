#!/usr/bin/env bash

# FIXME: check path
IMAGE_ROOT_PATH=${1:-"utils/docker/minimal"}
# TODO: implement a better arg parsing
GALAXY_URL=$2
GALAXY_API_KEY=$3
GALAXY_NETWORK=$4

# download wft4galaxy script
curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/install.sh | bash /dev/stdin .

# switch the Docker image context
cd ${IMAGE_ROOT_PATH}

# build docker image
./build-remote.sh --branch ${TRAVIS_BRANCH} && cd -

# FIXME: remove... it is just for debug
docker run --rm --network galaxy \
            ubuntu bash -c "apt-get update && apt-get install -y iputils-ping && timeout 10 ping 172.18.0.22"


# Run examples  # FIXME: change the repo and version TAGs
wft4galaxy-docker --skip-update --repository kikkomep --version minimal-travis-integration \
                  --network ${GALAXY_NETWORK} --debug \
                  --server ${GALAXY_URL} --api-key ${GALAXY_API_KEY} \
                  -f examples/change_case/workflow-test.yml