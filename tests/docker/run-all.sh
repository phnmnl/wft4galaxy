#!/usr/bin/env bash


set -o nounset

# with errexit, if any of the tests should result in a non-zero exit code
set -o errexit

# absolute path of the current script
script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# test minimal image
${script_path}/test-image.sh minimal "$@"

# test develop image
${script_path}/test-image.sh develop "$@"
