#!/usr/bin/env bash

# Define all the variables that this script can set
# (if they don't already exist)
export IMAGE="${IMAGE:-}"
export IMAGE_NAME="${IMAGE_NAME:-}"
export IMAGE_OWNER="${IMAGE_OWNER:-}"
export IMAGE_REGISTRY="${IMAGE_REGISTRY:-}"
export IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-}"
export IMAGE_TAG="${IMAGE_TAG:-}"

# parse existing IMAGE
if [[ -n "${IMAGE}" ]]; then

    echo "Using IMAGE=${IMAGE} to generate image info...">&2
    prefixes=$(echo ${IMAGE} | grep -o "/" | wc -l |  sed -e 's/^[[:space:]]*//')

    if [[ $prefixes -eq 0 ]]; then
        IMAGE_REGISTRY=""
        IMAGE_OWNER=""
        IMAGE_NAME="$(echo ${IMAGE} | sed -E "s/(.*):(.*)/\1/")"
        IMAGE_TAG="$(echo ${IMAGE} | sed -E "s/(.*):(.*)/\2/")"
    elif [[ $prefixes -eq 1 ]]; then
        IMAGE_REGISTRY=""
        IMAGE_OWNER="$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)/\1/")"
        IMAGE_NAME="$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)/\2/")"
        IMAGE_TAG="$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)/\3/")"
    elif [[ $prefixes -eq 2 ]]; then
        IMAGE_REGISTRY="$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\1/")"
        IMAGE_OWNER="$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\2/")"
        IMAGE_NAME="$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\3/")"
        IMAGE_TAG="$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\4/")"
    fi

elif [[ -n "${IMAGE_REPOSITORY}" ]]; then
    echo "Using IMAGE_REPOSITORY=${IMAGE_REPOSITORY} to generate image info...">&2
    prefixes=$(echo ${IMAGE_REPOSITORY} | grep -o "/" | wc -l |  sed -e 's/^[[:space:]]*//')

    IMAGE_REGISTRY=""
    if [[ $prefixes -eq 0 ]]; then
        IMAGE_OWNER=""
        IMAGE_NAME="$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)/\1/")"
    elif [[ $prefixes -eq 1 ]]; then
        IMAGE_OWNER="$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)\/(.*)/\1/")"
        IMAGE_NAME="$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)\/(.*)/\2/")"
    fi

else  # neither IMAGE_NAME nor IMAGE_REPOSITORY are set
    # set image owner
    if [[ -z "${IMAGE_OWNER}" ]]; then
        # map the git phnmnl repository to the Crs4 DockerHub repository
        if [[ ${GIT_OWNER} == "phnmnl" ]]; then
            IMAGE_OWNER="crs4"
        else
            IMAGE_OWNER="${GIT_OWNER}"
        fi
    fi

    # set IMAGE_NAME if not defined
    if [[ -z "${IMAGE_NAME}" ]]; then
        IMAGE_NAME="wft4galaxy"
    fi

    # if image tag isn't set, trying getting it from git
    if [[ -z "${IMAGE_TAG}" ]]; then
        if [[ -n ${GIT_BRANCH} || -n ${GIT_TAG} ]]; then
            IMAGE_TAG="${GIT_BRANCH}"
            if [[ -n ${GIT_TAG} ]]; then
                IMAGE_TAG="${GIT_TAG}" # preference to git tag name over branch
            fi
        fi
    fi

    # set image repository
    if [[ -z "${IMAGE_REPOSITORY}" ]]; then
        if [[ -n "${IMAGE_OWNER}" ]]; then
            IMAGE_REPOSITORY="${IMAGE_OWNER}/${IMAGE_NAME}"
        else
            IMAGE_REPOSITORY="${IMAGE_NAME}"
        fi
    fi
fi

# set image tag if not specified or detected
if [[ -z "${IMAGE_TAG}" ]]; then
    IMAGE_TAG="latest"
fi

# set image if not specified or detected
if [[ -z "${IMAGE}" ]]; then
    image=""
    if [[ -n ${IMAGE_REGISTRY} ]]; then
        image="${IMAGE_REGISTRY}/"
    fi
    if [[ -n ${IMAGE_OWNER} ]]; then
        image="${image}${IMAGE_OWNER}/"
    fi
    image="${image}${IMAGE_NAME}"
    if [[ -n ${IMAGE_TAG} ]]; then
        image="${image}:${IMAGE_TAG}"
    fi
    IMAGE="${image}"
fi

# log Docker image info
echo " - Docker image: ${IMAGE}" >&2
echo " - Docker image owner: ${IMAGE_OWNER}" >&2
echo " - Docker image name: ${IMAGE_NAME}" >&2
echo " - Docker image tag: ${IMAGE_TAG}" >&2
echo " - Docker image registry: ${IMAGE_REGISTRY}" >&2
echo " - Docker image repository: ${IMAGE_REPOSITORY}" >&2

