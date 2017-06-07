#!/usr/bin/env bash

# Define all the variables that this script can set
# (if they don't already exist)
export IMAGE="${IMAGE:-}"
export IMAGE_NAME="${IMAGE_NAME:-}"
export IMAGE_OWNER="${IMAGE_OWNER:-}"
export IMAGE_REGISTRY="${IMAGE_REGISTRY:-}"
export IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-}"
export IMAGE_TAG="${IMAGE_TAG:-}"
export IMAGE_TYPE="${IMAGE_TYPE:-}"

# configure image suffix
image_suffix=""
if [[ ${IMAGE_TYPE} == "develop" ]]; then
    image_suffix="-${IMAGE_TYPE}"
fi

# parse existing IMAGE or IMAGE_REPOSITORY env variable
pattern="((([[:alnum:]]*)\/)|((([[:alnum:]]*)\/)(([[:alnum:]]*)\/)))?([[:alnum:]]*)(\:([[:alnum:]]*))?$"
if [[ -n ${IMAGE} && ${IMAGE} =~ ${pattern} || -n ${IMAGE_REPOSITORY} && ${IMAGE_REPOSITORY} =~ ${pattern} ]]; then

    # log
    if [[ -n ${IMAGE} ]]; then
        echo "Using IMAGE=${IMAGE} to generate image info...">&2
    elif [[ -n ${IMAGE_REPOSITORY} ]]; then
        echo "Using IMAGE_REPOSITORY=${IMAGE_REPOSITORY} to generate image info...">&2
    fi

    # set minimal image info
    IMAGE_NAME="${BASH_REMATCH[9]}"
    IMAGE_TAG="${BASH_REMATCH[11]}" # it can be empty, but we fix it below

    # form with owner and image name
    if [[ -n ${BASH_REMATCH[2]} ]]; then
        IMAGE_OWNER="${BASH_REMATCH[3]}"
        IMAGE_REPOSITORY="${IMAGE_OWNER}/${IMAGE_NAME}"

    # extend form with registry and owner
    elif [[ -n ${BASH_REMATCH[4]} ]]; then
        IMAGE_REGISTRY="${BASH_REMATCH[6]}"
        IMAGE_OWNER="${BASH_REMATCH[8]}"
        IMAGE_REPOSITORY="${IMAGE_REGISTRY}/${IMAGE_OWNER}/${IMAGE_NAME}"
    fi

else  # neither IMAGE nor IMAGE_REPOSITORY are setted
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

    # append image suffix
    IMAGE_NAME="${IMAGE_NAME}${image_suffix}"

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

# replace not valid forward and backward slashes with dashes
IMAGE_TAG="${IMAGE_TAG//[\/\\]/-}"

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

