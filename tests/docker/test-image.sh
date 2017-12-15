#!/usr/bin/env bash

set -o nounset
set -o errexit

# absolute path of the current script
script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# base path for Docker images
image_root_path="${script_path}/../../utils/docker"

# print help
function print_usage(){
    echo "USAGE: $0 [--server URL] [--api-key API-KEY] [--network ADDRESS] { any options build-image.sh accepts }" >&2
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
  while test $# -gt 0
  do
      case "$1" in
          -h|--help)
              print_usage
              exit 0
              ;;
          --server )
              [ $# -ge 2 ] || { echo "Missing value for '$1'"; exit 1; }
              GALAXY_URL="$2"
              shift
              ;;
          --api-key)
              [ $# -ge 2 ] || { echo "Missing value for '$1'"; exit 1; }
              GALAXY_API_KEY="$2"
              shift
              ;;
          --network )
              [ $# -ge 2 ] || { echo "Missing value for '$1'"; exit 1; }
              GALAXY_NETWORK="$2"
              shift
              ;;
          --debug )
              debug="--debug"
              shift
              ;;
          *)
              OTHER_ARGS+=("${1}")
              ;;
      esac
      shift
  done

  # check required options
  local settings=(GALAXY_URL GALAXY_API_KEY)
  for s in ${settings[@]}; do
      if [[ -z ${!s} ]]; then
          echo "No ${s} provided." >&2
          exit 99
      fi
  done
}

function extract_build_image_info() { # args: (filename, tag)
  if [[ $# -ne 2 ]]; then
    error "BUG!  extract_build_image_tag called with $# arguments (expected 2)"
  fi
  local filename="${1}"
  local tag="${2}"

  local sed_expr="/${tag}/s/\s*${tag}\s*:\s*\([^,]*\),\?\s*/\1/p"
  local value="$(sed -n -e "${sed_expr}" "${filename}")"
  echo "Extracted ${tag}: '${value}'" &>2
  echo "${value}"

  return 0
}

########## main ###########

# absolute path of the current script
script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# initialize variables to default values, if any
GALAXY_URL=''
GALAXY_API_KEY=''
GALAXY_NETWORK=''

# other options to be passed to build-image.sh
OTHER_ARGS=()

# disable debug
debug=""

# parse args. An empty $@ will result in the empty string "" being passed, which is ok
# (we'll raise an error later for lack of mandatory arguments)
parse_args "${@:-}"

# copy the wft4galaxy script
docker_runner="${script_path}/../../wft4galaxy/app/docker_runner.py"

echo "Building docker image" >&2
build_image="${script_path}/../../utils/docker/build-image.sh"

# Use a temporary file to capture the name of the image being created
# `mktemp -t` is deprecated on Linux, but it gives us compatibility with both Linux and MacOS
tmpfile=$(mktemp -t wft4galaxy-test-image.XXXXX)
trap "rm -f '${tmpfile}'" EXIT # remove that file on exit

# fail if any step in the pipe files (we especially care about build-image.sh :-) )
set -o pipefail
# We want to capture the last section of the stdout from build-image.sh where it's
# going to print the name of the docker image it created. At the same time, we
# want the output to go to the console so that we can see what's going on.  >()
# is the syntax for bash's process substitution: tee writes to an "anonymous"
# pipe which is connected to sed's stdin. The sed command will delete everything
# up to and including the line with the marker

if [[ ${#OTHER_ARGS[@]} -eq 0 ]]; then
  # This works around bash's quirky behaviour of raising an error if nounset is on and
  # you expand an empty (but declared) array
  "${build_image}" | tee >(sed -e '1,/^=== build-image.sh complete ===$/d' > "${tmpfile}")
else
  "${build_image}" "${OTHER_ARGS[@]}" | tee >(sed -e '1,/^=== build-image.sh complete ===$/d' > "${tmpfile}")
fi

image_repo="$(extract_build_image_info "${tmpfile}" image_repository)"
image_tag="$(extract_build_image_info "${tmpfile}" image_tag)"

# array of arguments for the docker run
cmd_args=(--server "${GALAXY_URL}" --api-key "${GALAXY_API_KEY}" --skip-update)

if [[ -n "${image_repo}" ]]; then
  cmd_args+=(--repository "${image_repo}")
fi
if [[ -n "${image_tag}" ]]; then
  cmd_args+=(--tag "${image_tag}")
fi
if [[ -n "${debug}" ]]; then
  cmd_args+=("${debug}")
fi
if [[ -n "${GALAXY_NETWORK}" ]]; then
  cmd_args+=(--network "${GALAXY_NETWORK}")
fi

# finally, add the test definition argument
cmd_args+=(-f "${script_path}/../../examples/change_case/workflow-test.yml")

# uncomment for debug
#echo "Trying to contact Galaxy sever..."
#docker run --rm --network "${GALAXY_NETWORK}" \
#            ubuntu bash -c "apt-get update && apt-get install -y iputils-ping && timeout 5 ping 172.18.0.22"

# now run the tests
echo -e "CMD: ${docker_runner} ${cmd_args[@]}\n" >&2
# first turn off command error checking
set +o errexit
"${docker_runner}" "${cmd_args[@]}"
exit_code=$?

if [[ ${exit_code} -ne 0 ]]; then
  echo "Test failed (exit code: ${exit_code}" >&2
fi

exit ${exit_code}
