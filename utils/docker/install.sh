#!/bin/bash

set -o errexit
set -o nounset

# set default repo owner
DEFAULT_REPO="phnmnl/wft4galaxy"

# set default repo owner
DEFAULT_REPO_BRANCH="master"

# set default target folder
DEFAULT_TARGET_FOLDER="/usr/local/bin"

# empty temporary folder
TEMP_DIR=""

# print usage
function print_usage() {
    echo -e "\nUSAGE: ${0} [--repo <REPOSITORY>] [--branch <REPOSITORY_BRANCH>] [TARGET_FOLDER]"
    echo -e "\n\t Options:"
    echo -e "\t - REPOSITORY:        the name of the GitHub repository (default: \"${DEFAULT_REPO}\")"
    echo -e "\t - REPOSITORY_BRANCH: the branch name of the GitHub repository (default: \"${DEFAULT_REPO_BRANCH}\")"
    echo -e "\t - TARGET_FOLDER:     the path where to store the wft4galaxy-docker script (default: \"${DEFAULT_TARGET_FOLDER}\")"
}

# delete temporary files
function cleanup() {
	if [[ -n "${TEMP_DIR}" && -d "${TEMP_DIR}" ]]; then
		rm -rf "${TEMP_DIR}"
	fi
}

# set default values
REPO=${DEFAULT_REPO}
REPO_BRANCH=${DEFAULT_REPO_BRANCH}
TARGET_FOLDER=${DEFAULT_TARGET_FOLDER}

# parse arguments
OTHER_OPTS=''
while [ $# -gt 0 ]; do
    # Copy so we can modify it (can't modify $1)
    OPT="$1"
    # Detect argument termination
    if [ x"$OPT" = x"--" ]; then
            shift
            for OPT ; do
                    OTHER_OPTS="$OTHER_OPTS \"$OPT\""
            done
            break
    fi
    # Parse current opt
    while [ x"$OPT" != x"-" ] ; do
            case "$OPT" in
                  --repo=* )
                          REPO="${OPT#*=}"
                          shift
                          ;;
                  --repo )
                          REPO="$2"
                          shift
                          ;;
                  --branch=* )
                          REPO_BRANCH="${OPT#*=}"
                          shift
                          ;;
                  --branch )
                          REPO_BRANCH="$2"
                          shift
                          ;;
                  --help|-h )
                          print_usage
                          exit 0
                          ;;
                  * )
                          OTHER_OPTS="$OTHER_OPTS $OPT"
                          break
                          ;;
            esac
            # Check for multiple short options
            # NOTICE: be sure to update this pattern to match valid options
            NEXTOPT="${OPT#-[cfr]}" # try removing single short opt
            if [ x"$OPT" != x"$NEXTOPT" ] ; then
                    OPT="-$NEXTOPT"  # multiple short opts, keep going
            else
                    break  # long form, exit inner loop
            fi
    done
    # move to the next param
    shift
done

# update target folder if provided
ARGS=(${OTHER_OPTS})
if [[ ${#ARGS[@]} -eq 1 ]]; then
    TARGET_FOLDER=${ARGS[0]}
elif [[ ${#ARGS[@]} -gt 1 ]]; then
    echo -e "\nERROR: invalid syntax !!"
    print_usage
    exit 99
fi

# On exit, for whatever reason, try to clean up
trap "cleanup" EXIT INT ERR

# set source script
SOURCE_SCRIPT="https://raw.githubusercontent.com/${REPO}/${REPO_BRANCH}/wft4galaxy/app/docker_runner.py"

# download script
TEMP_DIR=$(mktemp -d)
TEMP_SCRIPT="${TEMP_DIR}/wft4galaxy-docker"
STATUS_CODE=$(curl --silent --output ${TEMP_SCRIPT} --write-out "%{http_code}" ${SOURCE_SCRIPT})
if [[ ${STATUS_CODE} -ne 200 ]]; then
    echo -e "\nERROR: Script ${SOURCE_SCRIPT} not found!"
    echo -e "       Check if you are using the proper REPOSITORY and BRANCH."
    print_usage
    exit 99
else
    chmod +x ${TEMP_SCRIPT}
    if [[ -w ${TARGET_FOLDER} ]]; then
        mv ${TEMP_SCRIPT} ${TARGET_FOLDER}/
    else
        echo -e "\nTo install 'wft4galaxy-docker' within the '${TARGET_FOLDER}' you need root permissions"
        sudo mv ${TEMP_SCRIPT} ${TARGET_FOLDER}/
    fi
    exit 0;
fi


