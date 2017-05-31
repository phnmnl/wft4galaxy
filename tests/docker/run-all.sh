#!/usr/bin/env bash

# absolute path of the current script
script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# test minimal image
${script_path}/test-image.sh minimal "$@"

# test develop image
${script_path}/test-image.sh develop "$@"