#!/usr/bin/env bash

# parse existing IMAGE
if [[ -n ${IMAGE} ]]; then
    export IMAGE_OWNER=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\1/")
    export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\2/")
    export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\3/")
fi

# parse existing IMAGE_REPOSITORY
if [[ -n ${IMAGE_REPOSITORY} ]]; then
    export IMAGE_OWNER=$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\1/")
    export IMAGE_NAME=$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\2/")
fi


# set image owner
if [[ -z ${IMAGE_OWNER} ]]; then
    if [[ -z ${GIT_OWNER} ]]; then
        echo "GIT_OWNER not found">&2
        exit -1
    fi

    # map the git phnmnl repository to the Crs4 DockerHub repository
    if [[ ${GIT_OWNER} == "phnmnl" ]]; then
        GIT_OWNER="crs4"
    fi
    export IMAGE_OWNER=${GIT_OWNER}
fi

# set IMAGE_NAME if not defined
if [[ -z ${IMAGE_NAME} ]]; then
    export IMAGE_NAME="wft4galaxy"
fi

# set image tag
if [[ -z ${GIT_BRANCH} && -z ${GIT_TAG} ]]; then
    echo "GIT_BRANCH or GIT_TAG not found">&2
    exit -1
fi
image_tag=${GIT_BRANCH}
if [[ -n ${GIT_TAG} ]]; then
    image_tag=${GIT_TAG}
fi
if [[ -n ${IMAGE_TAG_PREFIX} ]]; then
    image_tag="${IMAGE_TAG_PREFIX}-${image_tag}"
fi
export IMAGE_TAG=${image_tag}

# set image repository
if [[ -z ${IMAGE_REPOSITORY} ]]; then
    export IMAGE_REPOSITORY="${IMAGE_OWNER}/${IMAGE_NAME}"
fi

# set image repository
if [[ -z ${IMAGE} ]]; then
    export IMAGE="${IMAGE_OWNER}/${IMAGE_NAME}:${IMAGE_TAG}"
fi

# log git/docker info
echo " - Docker image: ${IMAGE}" >&2
echo " - Docker image owner: ${IMAGE_OWNER}" >&2
echo " - Docker image name: ${IMAGE_NAME}" >&2
echo " - Docker image tag prefix: ${IMAGE_TAG_PREFIX}" >&2
echo " - Docker image tag: ${IMAGE_TAG}" >&2
echo " - Docker image repository: ${IMAGE_REPOSITORY}" >&2

