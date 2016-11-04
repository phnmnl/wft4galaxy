#!/usr/bin/env bash
if [[ ${1} == "wft4galaxy" ]]; then
    shift
    wft4galaxy "$@"
elif [[ ${1} == "ipython" ]]; then
		ipython
elif [[ ${1} == "jupyter" ]]; then
		shift
		ipython notebook --ip=$(hostname) --no-browser --port 8888 "$@"
else
	/bin/bash "$@"
fi
