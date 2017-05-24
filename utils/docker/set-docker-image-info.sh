#!/usr/bin/env bash

# parse existing IMAGE
if [[ -n ${IMAGE} ]]; then

    echo "Using IMAGE=${IMAGE} to generate image info...">&2
    prefixes=$(echo ${IMAGE} | grep -o "/" | wc -l |  sed -e 's/^[[:space:]]*//')

    if [[ $prefixes -eq 0 ]]; then
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*):(.*)(\.git)/\1/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*):(.*)(\.git)/\2/")
        export IMAGE_OWNER=""
        export IMAGE_REGISTRY=""
    elif [[ $prefixes -eq 1 ]]; then
        export IMAGE_REGISTRY=""
        export IMAGE_OWNER=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\1/")
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\2/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\3/")
    elif [[ $prefixes -eq 2 ]]; then
        export IMAGE_REGISTRY=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)(\.git)/\1/")
        export IMAGE_OWNER=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)(\.git)/\2/")
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)(\.git)/\3/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)(\.git)/\4/")
    fi

elif [[ -n ${IMAGE_REPOSITORY} ]]; then

    echo "Using IMAGE_REPOSITORY=${IMAGE_REPOSITORY} to generate image info...">&2
    prefixes=$(echo ${IMAGE_REPOSITORY} | grep -o "/" | wc -l |  sed -e 's/^[[:space:]]*//')

    export IMAGE_REGISTRY=""
    if [[ $prefixes -eq 0 ]]; then
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*):(.*)(\.git)/\1/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*):(.*)(\.git)/\2/")
        export IMAGE_OWNER=""
        export IMAGE_REGISTRY=""
    elif [[ $prefixes -eq 1 ]]; then
        export IMAGE_REGISTRY=""
        export IMAGE_OWNER=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\1/")
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\2/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)(\.git)/\3/")
    fi

# if neither IMAGE_NAME or IMAGE_REPOSITORY are setted
else
    echo "Using Git repository info to generate image info...">&2

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
    if [[ -z ${IMAGE_TAG} ]]; then
        if [[ -z ${GIT_BRANCH} && -z ${GIT_TAG} ]]; then
            echo "GIT_BRANCH or GIT_TAG not found">&2
            exit -1
        fi
        image_tag=${GIT_BRANCH}
        if [[ -n ${GIT_TAG} ]]; then
            image_tag=${GIT_TAG}
        fi
        export IMAGE_TAG=${image_tag}
    fi

    # set image repository
    if [[ -z ${IMAGE_REPOSITORY} ]]; then
        export IMAGE_REPOSITORY="${IMAGE_OWNER}/${IMAGE_NAME}"
    fi
fi

# set image repository
if [[ -z ${IMAGE} ]]; then
    if [[ -n ${IMAGE_REGISTRY} ]]; then
        export IMAGE="${IMAGE_REGISTRY}/${IMAGE_OWNER}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        export IMAGE="${IMAGE_OWNER}/${IMAGE_NAME}:${IMAGE_TAG}"
    fi
fi

# log Docker image info
echo " - Docker image: ${IMAGE}" >&2
echo " - Docker image owner: ${IMAGE_OWNER}" >&2
echo " - Docker image name: ${IMAGE_NAME}" >&2
echo " - Docker image tag: ${IMAGE_TAG}" >&2
echo " - Docker image registry: ${IMAGE_REGISTRY}" >&2
echo " - Docker image repository: ${IMAGE_REPOSITORY}" >&2

