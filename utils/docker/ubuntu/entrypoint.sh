#!/usr/bin/env bash
if [[ ${1} == "wft4galaxy" ]]; then
    shift
    wft4galaxy "$@"
elif [[ ${1} == "ipython" ]]; then
		ipython
elif [[ ${1} == "jupyter" ]]; then
		shift
		ipython notebook --ip=$(hostname) --no-browser --port 8888 "$@"
elif [[ ${1} == "bash" ]]; then
    shift
    /bin/bash "$@"
else
	  /bin/bash "$@"
fi
