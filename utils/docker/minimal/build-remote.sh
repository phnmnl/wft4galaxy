#!/usr/bin/env bash

# absolute path of the current script
script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# set prefix for distinguishing minimal from develop image (used by the 'set-docker-image-info' script)
export IMAGE_TAG_PREFIX="minimal"

# set git && image info
source ${script_path}/../set-git-repo-info.sh "$@"
source ${script_path}/../set-docker-image-info.sh

# Need to cd into this script's directory because image-config assumes it's running within it
cd "${script_path}"

# load git/docker info
source "${script_path}/../image-config.sh"

if [ -z "${git_branch}" -o -z "${git_url}" ]; then
  echo "Error fetching remote repository information :-(  Try specifying it on the command line" >&2
  exit 1
fi

# build the Docker image
docker build --build-arg git_branch=${GIT_BRANCH} --build-arg git_url=${GIT_HTTPS} -t ${IMAGE} .

# restore the original path
cd -
