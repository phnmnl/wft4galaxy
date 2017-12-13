#!/usr/bin/env bash

set -o nounset
set -o errexit

function print_usage(){
    (   echo "USAGE: $0 [ --image REG/OWNER/NAME[:TAG] ] [ --image-repository OWNER/NAME[:TAG] ] \\"
        echo "          [-o|--image-owner OWNER] [-n|--image-name NAME] [-t|--image-tag TAG] \\"
        echo "          [ --local-copy | --repo-url URL --repo-branch BRANCH ] < minimal | develop >"
        echo
        echo "If no arguments are provided, this script will try to get the"
        echo "required repository information from the local repository itself") >&2
}


function error() {
  if [[ $# -gt 0 ]]; then
    echo "$@" >&2
  else
    echo "Sorry.  There's been an error!" >&2
  fi
  exit 2
}

function usage_error() {
  if [[ $# -gt 0 ]]; then
    echo "$@" >&2
  fi
  print_usage
  exit 2
}

function parse_args() {
  # this function parses the arguments it receives in $@ and sets variables
  local image_type=""
  while test $# -gt 0
  do
      case "$1" in
          -h|--help)
              print_usage
              exit 0
              ;;
          --image)
              IMAGE="${2}"
              shift
              ;;
          --image-repository)
              IMAGE_REPOSITORY="${2}"
              shift
              ;;
          -r|--image-registry)
              IMAGE_REGISTRY=$2
              shift
              ;;
          -o|--image-owner)
              IMAGE_OWNER=$2
              shift
              ;;
          -n|--image-name)
              IMAGE_NAME=$2
              shift
              ;;
          -t|--image-tag)
              IMAGE_TAG=$2
              shift
              ;;
          --url|--repo-url)
              repo_url="--url $2"
              shift
              ;;
          --branch|--repo-branch)
              repo_branch="--branch $2"
              shift
              ;;
          --local-copy)
              local_copy="true"
              ;;
          --*)
              print_usage
              exit 99
              ;;
          *)
              # support only the first argument; skip all remaining
              if [[ -z ${image_type} ]]; then
                  image_type=${1}
              fi
              ;;
      esac
      shift
  done

  if [[ -z "${image_type}" ]]; then
      echo "No image type provided. Using the default: ${IMAGE_TYPE}" >&2
  elif [[ ${image_type} != "minimal" && ${image_type} != "develop" ]]; then
      echo -e "\nERROR: '${image_type}' not supported! Use 'minimal' or 'develop'."
      exit 99
  else
      IMAGE_TYPE="${image_type}"
  fi

  if [[ "${local_copy}" = "true" && ( -n "${repo_url}" || -n "${repo_branch}" ) ]]; then
    usage_error "--local-copy is mutually exclusive with repository url and/or branch"
  fi

  if [[ "${local_copy}" = "true" && ( -z "${IMAGE}" && -z "${IMAGE_REPOSITORY}" && -z "${IMAGE_OWNER}" ) ]]; then
    echo "Sorry.  For local mode you need to specify an --image-owner or an --image-repository or an --image" >&2
    exit 1
  fi

  if [[ "${local_copy}" == "true" ]]; then
    echo "Buildind an image using the current local project state" >&2
    echo "=*=*=*=*=*=* WARNING: Your Docker image could include uncommitted changes! *=*=*=*=*=*=" >&2
  else
    echo "Building an image using a wft4galaxy pulled from a git repository" >&2
  fi
}

function build_local_image() {
  if [[ -z "${IMAGE}" && -z "${IMAGE_REPOSITORY}" && -z "${IMAGE_OWNER}" ]]; then
    echo "BUG! Trying to build a local image without image information" >&2
    exit 2
  fi

  # assemble any missing image info
  source ${script_path}/set-docker-image-info.sh

  src_dir_root="${script_path}/../../"
  # Try to verify that we have the right directory
  if [[ ! -d "${src_dir_root}/wft4galaxy" || ! -d "${src_dir_root}/utils" ]]; then
    error "I think the wft4galaxy root directory should be '${src_dir_root}' but I can't \n" \
          "find the 'wft4galaxy' and 'utils' subdirectories there. Aborting!"
  fi

  cd "${src_dir_root}" > /dev/null
  docker build . -f "${script_path}/${IMAGE_TYPE}/Dockerfile.local" -t ${IMAGE}
}

function build_repo_image() {
  # set git && image info
  source ${script_path}/set-git-repo-info.sh ${repo_url} ${repo_branch}
  source ${script_path}/set-docker-image-info.sh

  cd "${src_dir_root}" > /dev/null
  # build the Docker image
  docker build . -f "${script_path}/${IMAGE_TYPE}/Dockerfile.git" \
		     --build-arg git_branch=${GIT_BRANCH} --build-arg git_url=${GIT_HTTPS} -t ${IMAGE}
}

########## main ###########

# absolute path of the current script
script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# initialize variables to default values, if any
IMAGE=""
IMAGE_REPOSITORY=""
IMAGE_REGISTRY=""
IMAGE_OWNER=""
IMAGE_NAME=""
IMAGE_TAG=""
IMAGE_TYPE="minimal"
repo_url=""
repo_branch=""
local_copy="false"

parse_args "${@}"

if [[ "${local_copy}" = "true" ]]; then
  build_local_image
else
  build_repo_image
fi

# restore the original path
cd - > /dev/null

echo "Built image: ${IMAGE}" &>2

# Don't modify this output without updating test-image.sh!"
Template="{
image : %s,
image_repository : %s,
image_registry : %s,
image_owner : %s,
image_name : %s,
image_tag : %s,
image_type : %s
}\n"
echo "=== build-image.sh complete ==="
printf "${Template}" "${IMAGE}" "${IMAGE_REPOSITORY}" "${IMAGE_REGISTRY}" \
                     "${IMAGE_OWNER}" "${IMAGE_NAME}" "${IMAGE_TAG}" "${IMAGE_TYPE}"
