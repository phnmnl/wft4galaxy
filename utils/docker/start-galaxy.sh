#!/usr/bin/env bash

# set args
export GALAXY_CONFIG_MASTER_API_KEY=${1:-"HSNiugRFvgT574F43jZ7N9F3"}
export GALAXY_PORT=${2:-30700}
export GALAXY_DOCKER_HOST=${3:-"localhost"}
export GALAXY_CONTAINER_NAME=${4:-"galaxy-server"}

# start Dockerized Galaxy
docker run -d -e GALAXY_CONFIG_MASTER_API_KEY=${GALAXY_CONFIG_MASTER_API_KEY=HSNiugRFvgT574F43jZ7N9F3} \
              -p ${GALAXY_PORT}:80 -p 8021:21 -p 8022:22 \
              --name ${GALAXY_CONTAINER_NAME} \
              bgruening/galaxy-stable

# set the Galaxy URL
export GALAXY_URL="http://${GALAXY_DOCKER_HOST}:${GALAXY_PORT}"

# wait for Galaxy
printf '\nWaiting for Galaxy...'
until $(curl --output /dev/null --silent --head --fail ${GALAXY_URL}); do
    printf '.'
    sleep 5
done
printf ' Started\n'

# Galaxy info
printf "\nGalaxy server running @ ${GALAXY_URL}\n"

