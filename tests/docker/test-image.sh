#!/usr/bin/env bash

set -o nounset
set -o errexit

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

# init argument variables
image_type=''
GALAXY_URL=''
GALAXY_API_KEY=''
GALAXY_NETWORK=''
repo_url=''
GIT_BRANCH=''
repo_branch=''

# options
opts="$@"

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
        --url|--repo-url)
            [ $# -ge 2 ] || { echo "Missing value for '$1'"; exit 1; }
            repo_url="--url $2"
            shift
            ;;
        --branch|--repo-branch)
            [ $# -ge 2 ] || { echo "Missing value for '$1'"; exit 1; }
            GIT_BRANCH=$2
            repo_branch="--branch $2"
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
        echo "No ${s} provided." >&2
        exit 1
    fi
done


# extract git info & Docker image name
source ${image_root_path}/set-git-repo-info.sh ${repo_url} ${repo_branch}
source ${image_root_path}/set-docker-image-info.sh

# download wft4galaxy script
owner=${GIT_OWNER:-"phnmnl"}
branch=${GIT_BRANCH:-"develop"}
curl -s https://raw.githubusercontent.com/${owner}/wft4galaxy/${branch}/utils/docker/install.sh | bash /dev/stdin --repo "${owner}/wft4galaxy" --branch ${branch} .
echo "Downloaded 'wft4galaxy-docker' Github repository: ${owner}/wft4galaxy (branch: ${branch})" >&2

# switch the Docker image context
cd ${image_root_path} > /dev/null

# build docker image
echo "${image_root_path}/${image_type}/build.sh ${opts}" >&2
"${image_root_path}/${image_type}/build.sh" ${repo_branch}
cd - > /dev/null

# set optional arguments
cmd_other_opts="--repository ${IMAGE_OWNER}/wft4galaxy --skip-update ${debug}"
if [[ -n ${IMAGE_TAG} ]]; then
    cmd_other_opts="${cmd_other_opts} --tag ${IMAGE_TAG}"
fi
if [[ -n ${GALAXY_NETWORK} ]]; then
    cmd_other_opts="${cmd_other_opts} --network ${GALAXY_NETWORK}"
fi

# uncomment for debug
#echo "Trying to contact Galaxy sever..."
#docker run --rm --network ${GALAXY_NETWORK} \
#            ubuntu bash -c "apt-get update && apt-get install -y iputils-ping && timeout 5 ping 172.18.0.22"

# build cmd
base_cmd="./wft4galaxy-docker ${cmd_other_opts} --server ${GALAXY_URL} --api-key ${GALAXY_API_KEY}"
cmd="${base_cmd} -f examples/change_case/workflow-test.yml"
echo -e "CMD: ${cmd}\n">&2

# turn off command error checking
set +o errexit

# run test
${cmd} 
exit_code=$?

# cleanup
rm -f wft4galaxy-docker

if [ ${exit_code} -ne 0 ]; then
    echo "Test failed (exit code: ${exit_code}" >&2
fi

exit ${exit_code}
