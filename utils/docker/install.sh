#!/bin/bash

set -e

# set default repo owner
DEFAULT_REPO_OWNER="phnmnl"

# set default repo owner
DEFAULT_REPO_BRANCH="develop"

# set default target folder
DEFAULT_TARGET_FOLDER="/usr/local/bin"

# print usage
function print_usage(){
    echo -e "\nUSAGE: ${0} [--owner <REPO_OWNER>] [--branch <REPO_BRANCH>] [TARGET_FOLDER]"
    echo -e "\n\t Options:"
    echo -e "\t - TARGET_FOLDER: the path where to store the wft4galaxy-docker script (default: \"${DEFAULT_TARGET_FOLDER}\")"
    echo -e "\t - REPO_OWNER:    the owner name of the GitHub repository (default: \"${DEFAULT_REPO_OWNER}\")"
    echo -e "\t - REPO_BRANCH:   the branch name of the GitHub repository (default: \"${DEFAULT_REPO_BRANCH}\")"
}

# set default values
REPO_OWNER=${DEFAULT_REPO_OWNER}
REPO_BRANCH=${DEFAULT_REPO_BRANCH}
TARGET_FOLDER=${DEFAULT_TARGET_FOLDER}

# parse arguments
while [ -n "$1" ]; do
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
                  --owner=* )
                          REPO_OWNER="${OPT#*=}"
                          shift
                          ;;
                  --owner )
                          REPO_OWNER="$2"
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
    exit -1
fi

# set source script
SOURCE_SCRIPT="https://raw.githubusercontent.com/${REPO_OWNER}/wft4galaxy/${REPO_BRANCH}/wft4galaxy/app/docker_runner.py"

# download script
TEMP_SCRIPT="/tmp/wft4galaxy-docker"
STATUS_CODE=$(curl --silent --output ${TEMP_SCRIPT} --write-out "%{http_code}" ${SOURCE_SCRIPT})
if [[ ${STATUS_CODE} -ne 200 ]]; then
    echo -e "\nERROR: Script ${SOURCE_SCRIPT} not found!"
    echo -e "       Check if you are using the proper repository OWNER and BRANCH."
    print_usage
    exit -1
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

