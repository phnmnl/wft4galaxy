#!/usr/bin/env bash
if [[ ${1} == "bash" ]]; then
    shift
    /bin/bash "$@"
else
    wft4galaxy "$@"
fi