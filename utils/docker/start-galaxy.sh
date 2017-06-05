#!/usr/bin/env bash

set -o errexit
set -o nounset

# Docker settings
docker_image="bgruening/galaxy-stable"
docker_host="localhost"
network=""
ip=""
master_api_key=""
port=80
container_name="galaxy-server"
debug="false"
max_wait_time=$((5*60)) # seconds


function print_usage(){
    (echo -e "\n USAGE: start-galaxy.sh [--docker-host <IP>] [--container-name <NAME>] [--master-api-key <API-KEY>]"
     echo -e "                        [--network <DOCKER_NETWORK>] [--ip <CONTAINER_ADDRESS>] [--port <GALAXY_HTTP_PORT>]"
     echo -e "                        [-h|--help]\n ") >&2
}

function usage_error() {
  print_usage
  exit 1
}

function get_opt_value() {
  if [ $# -le 1 ]; then
    echo "Missing value for option ${1}" >&2
    usage_error # never returns
  fi

  local value="${2}"
  if [[ "${value}" == --* ]]; then # need [[ for wildcard matching
    echo "Missing value for option ${1} (found other option '${value}')" >&2
    usage_error # never returns
  fi

  echo ${value}
  return 0
}

######### main ##########

OTHER_OPTS=''
while [ $# -gt 0 ]; do
    OPT="$1"
    # Detect argument termination
    if [ x"$OPT" == x"--" ]; then
            shift
            for OPT ; do
                    OTHER_OPTS="$OTHER_OPTS \"$OPT\""
            done
            break
    fi
    # Parse current opt
    case "$OPT" in
          --docker-host=* )
                  docker_host="${OPT#*=}"
                  ;;
          --docker-host )
                  docker_host="$(get_opt_value "${@}")"
                  shift
                  ;;
          --network=* )
                  network="${OPT#*=}"
                  ;;
          --network )
                  network="$(get_opt_value "${@}")"
                  shift
                  ;;
          --ip=* )
                  ip="${OPT#*=}"
                  ;;
          --ip )
                  ip="$(get_opt_value "${@}")"
                  shift
                  ;;
          --port=* )
                  port="${OPT#*=}"
                  ;;
          --port )
                  port="$(get_opt_value "${@}")"
                  shift
                  ;;
          --master-api-key=* )
                  master_api_key="${OPT#*=}"
                  ;;
          --master-api-key )
                  master_api_key="$(get_opt_value "${@}")"
                  shift
                  ;;
          --container-name=* )
                  container_name="${OPT#*=}"
                  ;;
          --container-name )
                  container_name="$(get_opt_value "${@}")"
                  shift
                  ;;
          --debug )
                debug="true"
                ;;
          -h|--help )
                print_usage
                exit 0
                ;;
          *)
                OTHER_OPTS="$OTHER_OPTS $OPT"
                break
                ;;
    esac

    # move to the next param
    shift
done


# Docker options
docker_options=""
if [[ -n ${master_api_key} ]]; then
    docker_options="${docker_options} -e GALAXY_CONFIG_MASTER_API_KEY=${master_api_key}"
fi

if [[ -n ${network} ]]; then
    docker_options="${docker_options} --network ${network}"
fi

if [[ -n ${ip} ]]; then
    docker_options="${docker_options} --ip ${ip}"
fi

if [[ -n ${container_name} ]]; then
    docker_options="${docker_options} --name ${container_name}"
fi


# set the Galaxy URL
galaxy_exposed="${docker_host}:${port}"
#export GALAXY_URL=${GALAXY_URL//[[:blank:]]/}

# Build Docker command
docker_cmd="docker run -d ${docker_options} -p ${galaxy_exposed}:80 ${docker_image}"

if [[ ${debug} == "true" ]]; then
    echo "docker_image=    ${docker_image}"
    echo "docker_host=     ${docker_host}"
    echo "network=         ${network}"
    echo "ip=              ${ip}"
    echo "master_api_key=  ${master_api_key}"
    echo "port=            ${port}"
    echo "container_name=  ${container_name}"
    echo "debug=           ${debug}"
    echo "max_wait_time=   ${max_wait_time}"
    echo -e "\nDocker Command: ${docker_cmd}"
fi

# start Dockerized Galaxy
# If this fails the script should exit with non-zero because of errexit
${docker_cmd}

# wait for Galaxy
wait_time=0
sleep_time=5
printf "\nWaiting for Galaxy @ ${GALAXY_URL} ..."
until $(curl --output /dev/null --silent --head --fail ${GALAXY_URL}); do
    printf '.'
    sleep ${sleep_time}
    wait_time=$((${wait_time} + ${sleep_time}))
    if [ ${wait_time} -ge ${max_wait_time} ]; then
        (printf "There seems to be a problem starting Galaxy.\n"
         printf "We've waitedf or %d seconds so far and it's still not answering\n"
         printf "Giving up\n" ) >&2
        exit 2
    fi
done
printf ' Started\n'

# Galaxy info
printf "\nGalaxy server running @ ${GALAXY_URL}\n"

exit 0
