#!/usr/bin/env bash

## configure galaxy server
#export GALAXY_CONFIG_MASTER_API_KEY=${1:-"HSNiugRFvgT574F43jZ7N9F3"}
#export GALAXY_PORT=${2:-30700}
#export GALAXY_DOCKER_HOST=${3:-"localhost"}
#export GALAXY_CONTAINER_NAME=${4:-"galaxy-server"}
#export GALAXY_USERNAME=${5:-"wft4galaxy"}
#export GALAXY_USER_PASSWORD=${6:-"wft4galaxy-tester"}
#export GALAXY_USER_EMAIL=${7:-"wft4galaxy@wft.it"}
#
## path to folder containing utilities for starting Dockerized Galaxy
#UTILS_PATH="././../../utils/"
#
## start galaxy
#source ${UTILS_PATH}/start-galaxy.sh ${GALAXY_CONFIG_MASTER_API_KEY} \
#                                ${GALAXY_PORT} \
#                                ${GALAXY_DOCKER_HOST} \
#                                ${GALAXY_CONTAINER_NAME}
#
## config user
#./create_galaxy_user.py --server ${GALAXY_URL} --api-key ${GALAXY_CONFIG_MASTER_API_KEY} --with-api-key \
#                        ${GALAXY_USERNAME} ${GALAXY_USER_PASSWORD} ${GALAXY_USER_EMAIL}


GALAXY_API_KEY=${1}
echo "Galaxy URL: ${GALAXY_API_KEY}"