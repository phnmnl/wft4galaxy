#!/usr/bin/env bash

set -e

# absolute path of the current script
script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# base path for Docker images
image_root_path="${script_path}/../../utils/docker"

# print help
function print_usage(){
    (   echo "USAGE: $0 [--server URL] [--api-key API-KEY] [--network ADDRESS] "
        echo "          [-r|--image-registry REGISTRY] [-o|--image-owner OWNER] [-n|--image-name NAME] [-t|--image-tag TAG]"
        echo "          {minimal,develop}"
        echo ""
        echo "If no options related to the Docker image are provided, this script will try to get the"
        echo "required image information from the local repository itself") >&2
}

# disable debug
debug=""

# parse args
while test $# -gt 0
do
    case "$1" in
        -h|--help)
            print_usage
            exit 0
            ;;
        --server )
            GALAXY_URL=$2
            shift
            ;;
        --api-key)
            GALAXY_API_KEY=$2
            shift
            ;;
        --network )
            GALAXY_NETWORK=$2
            shift
            ;;
        -r|--image-registry)
            export IMAGE_REGISTRY=$2
            shift
            ;;
        -o|--image-owner)
            export IMAGE_OWNER=$2
            shift
            ;;
        -n|--image-name)
            export IMAGE_NAME=$2
            shift
            ;;
        -t|--image-tag)
            export IMAGE_TAG=$2
            shift
            ;;
        --debug )
            debug="--debug"
            shift
            ;;
        --*)
            print_usage
            exit -1
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

# check required options
settings=(image_type GALAXY_URL GALAXY_API_KEY)
for s in ${settings[@]}; do
    if [[ -z ${!s} ]]; then
        echo "No ${s} provided."
        exit -1
    fi
done

# download wft4galaxy script
curl -s https://raw.githubusercontent.com/phnmnl/wft4galaxy/develop/utils/docker/install.sh | bash /dev/stdin .

# switch the Docker image context
cd ${image_root_path}

# build docker image
"${image_root_path}/${image_type}/build.sh" && cd -

# set optional arguments
cmd_other_opts="--skip-update ${debug}"
if [[ -n ${IMAGE_REPOSITORY} ]]; then
    cmd_other_opts="${cmd_other_opts} --repository ${IMAGE_REPOSITORY}"
fi
if [[ -n ${IMAGE_TAG} ]]; then
    # TODO: update version to tag
    cmd_other_opts="${cmd_other_opts} --version ${IMAGE_TAG}"
fi
if [[ -n ${GALAXY_NETWORK} ]]; then
    cmd_other_opts="${cmd_other_opts} --network ${GALAXY_NETWORK}"
fi

# uncomment for debug
#echo "Trying to contact Galaxy sever..."
#docker run --rm --network ${GALAXY_NETWORK} \
#            ubuntu bash -c "apt-get update && apt-get install -y iputils-ping && timeout 5 ping 172.18.0.22"

# build cmd
base_cmd="wft4galaxy-docker ${cmd_other_opts} --server ${GALAXY_URL} --api-key ${GALAXY_API_KEY}"
cmd="${base_cmd} -f examples/change_case/workflow-test.yml"
echo "CMD: ${cmd}">&2

# run test
${cmd}
