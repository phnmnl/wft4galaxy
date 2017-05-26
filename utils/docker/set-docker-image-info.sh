#!/usr/bin/env bash

# parse existing IMAGE
if [[ -n ${IMAGE} ]]; then

    echo "Using IMAGE=${IMAGE} to generate image info...">&2
    prefixes=$(echo ${IMAGE} | grep -o "/" | wc -l |  sed -e 's/^[[:space:]]*//')

    if [[ $prefixes -eq 0 ]]; then
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*):(.*)/\1/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*):(.*)/\2/")
        export IMAGE_OWNER=""
        export IMAGE_REGISTRY=""
    elif [[ $prefixes -eq 1 ]]; then
        export IMAGE_REGISTRY=""
        export IMAGE_OWNER=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)/\1/")
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)/\2/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*):(.*)/\3/")
    elif [[ $prefixes -eq 2 ]]; then
        export IMAGE_REGISTRY=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\1/")
        export IMAGE_OWNER=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\2/")
        export IMAGE_NAME=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\3/")
        export IMAGE_TAG=$(echo ${IMAGE} | sed -E "s/(.*)\/(.*)\/(.*):(.*)/\4/")
    fi

elif [[ -n ${IMAGE_REPOSITORY} ]]; then

    echo "Using IMAGE_REPOSITORY=${IMAGE_REPOSITORY} to generate image info...">&2
    prefixes=$(echo ${IMAGE_REPOSITORY} | grep -o "/" | wc -l |  sed -e 's/^[[:space:]]*//')

    export IMAGE_REGISTRY=""
    if [[ $prefixes -eq 0 ]]; then
        export IMAGE_NAME=$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)/\1/")
        export IMAGE_OWNER=""
    elif [[ $prefixes -eq 1 ]]; then
        export IMAGE_OWNER=$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)\/(.*)/\1/")
        export IMAGE_NAME=$(echo ${IMAGE_REPOSITORY} | sed -E "s/(.*)\/(.*)/\2/")
    fi

# if neither IMAGE_NAME or IMAGE_REPOSITORY are setted
else

    # set image owner
    if [[ -z ${IMAGE_OWNER} ]]; then
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
        if [[ -n ${GIT_BRANCH} || -n ${GIT_TAG} ]]; then
            image_tag=${GIT_BRANCH}
            if [[ -n ${GIT_TAG} ]]; then
                image_tag=${GIT_TAG}
            fi
        else
            image_tag="latest"
        fi
        export IMAGE_TAG=${image_tag}
    fi

    # set image repository
    if [[ -z ${IMAGE_REPOSITORY} ]]; then
        if [[ -n ${IMAGE_OWNER} ]]; then
            export IMAGE_REPOSITORY="${IMAGE_OWNER}/${IMAGE_NAME}"
        else
            export IMAGE_REPOSITORY="${IMAGE_NAME}"
        fi
    fi
fi

# set image tag if doesn't specified or detected
if [[ -z ${IMAGE_TAG} ]]; then
    export IMAGE_TAG="latest"
fi

# set image repository
if [[ -z ${IMAGE} ]]; then
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
    export IMAGE=${image}
fi

# log Docker image info
echo " - Docker image: ${IMAGE}" >&2
echo " - Docker image owner: ${IMAGE_OWNER}" >&2
echo " - Docker image name: ${IMAGE_NAME}" >&2
echo " - Docker image tag: ${IMAGE_TAG}" >&2
echo " - Docker image registry: ${IMAGE_REGISTRY}" >&2
echo " - Docker image repository: ${IMAGE_REPOSITORY}" >&2

