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

  value="${2}"
  if [[ "${value}" == --* ]]; then # need [[ for wildcard matching
    echo "Missing value for option ${1} (found other option '${value}')" >&2
    usage_error # never returns
  fi

  echo ${value}
  shift
  return 0
}

function do_argument_parsing() {
  #
  # This function  modifies variables set at the script's global scope
  #

  if [ $# -le 0 ]; then
    return 0
  fi

  OTHER_OPTS=''
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
                    --docker-host=* )
                            docker_host="${OPT#*=}"
                            ;;
                    --docker-host )
                            docker_host="$(get_opt_value)"
                            ;;
                    --network=* )
                            network="${OPT#*=}"
                            ;;
                    --network )
                            network="$(get_opt_value)"
                            ;;
                    --ip=* )
                            ip="${OPT#*=}"
                            ;;
                    --ip )
                            ip="$(get_opt_value)"
                            ;;
                    --port=* )
                            port="${OPT#*=}"
                            ;;
                    --port )
                            port="$(get_opt_value)"
                            ;;
                    --master-api-key=* )
                            master_api_key="${OPT#*=}"
                            ;;
                    --master-api-key )
                            master_api_key="$(get_opt_value)"
                            ;;
                    --container-name=* )
                            container_name="${OPT#*=}"
                            ;;
                    --container-name )
                            container_name="$(get_opt_value)"
                            ;;
                    --debug )
                          debug="true"
                          shift
                          ;;
                    -h|--help )
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
}

######### main ##########
do_argument_parsing

# Docker options
docker_options=""
if [[ -n ${master_api_key} ]]; then
    docker_options="${docker_options}-e GALAXY_CONFIG_MASTER_API_KEY=${master_api_key}"
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
