#!/bin/bash

# print usage
function print_usage(){
    echo -e "\nUsage: wft4galaxy-docker [-m|--mode <MODE>] [-e|--entrypoint <MODE_ENTRYPOINT>] [GLOBAL_OPTIONS] [ENTRYPOINT_OPTIONS] [DOCKER_OPTIONS]"
    echo -e "       e.g.: wft4galaxy-docker -m production -e wft4galaxy [wft4galaxy_OPTIONS] (default)"
    echo -e "       e.g.: wft4galaxy-docker [wft4galaxy_OPTIONS] (default)\n"

    echo -e "    MODEs: "
    echo -e "\t  1) production (default)"
    echo -e "\t  2) develop\n"

    echo -e "    MODE ENTRYPOINT_OPTIONs:"
    echo -e "\t  * PRODUCTION MODE: bash, wft4galaxy (default)"
    echo -e "\t  * DEVELOP MODE:    bash (default), ipython, jupyter, wft4galaxy\n"

    echo -e "    GLOBAL OPTIONs:"
    echo -e "\t  -h, --help            show this help message and exit"
    echo -e "\t  --server=SERVER       Galaxy server URL"
    echo -e "\t  --api-key=API_KEY     Galaxy server API KEY\n"

    echo -e "    DOCKER OPTIONs:"
    echo -e "\t  every additional option to pass to the Docker Engine when it starts a wft4galaxy container"
    echo -e "\t  e.g., -v myhost-folder:/container-host-folder\n"

    echo -e "    ENTRYPOINT OPTIONs:"
    echo -e "\t  *) jupyter options:"
    echo -e "\t\t  -p, --port            jupyter port (default: 9876)"
    echo -e "\n\t  *) wft4galaxy options:"
    echo -e "\t\t  --enable-logger       Enable log messages"
    echo -e "\t\t  --debug               Enable debug mode"
    echo -e "\t\t  --disable-cleanup     Disable cleanup"
    echo -e "\t\t  -o OUTPUT, --output=OUTPUT"
    echo -e "\t\t                        absolute path of the output folder"
    echo -e "\t\t  -f FILE, --file=FILE  YAML configuration file of workflow tests"
}

# set Docker image
DOCKER_REGISTRY="crs4"
DOCKER_IMAGE="wft4galaxy"

# set defaults
GALAXY_SERVER=${BIOBLEND_GALAXY_URL}
GALAXY_API_KEY=${BIOBLEND_GALAXY_API_KEY}
JUPYTER_PORT=9876
MODE="production"
BASE_OS="alpine"
OUTPUT_FOLDER="results"

# parse arguments
while [ -n "$1" ]; do
        # Copy so we can modify it (can't modify $1)
        OPT="$1"
        # Detect argument termination
        if [ x"$OPT" = x"--" ]; then
                shift
                for OPT ; do
                        DOCKER_OPTS="$DOCKER_OPTS \"$OPT\""
                done
                break
        fi
        # Parse current opt
        while [ x"$OPT" != x"-" ] ; do
                case "$OPT" in
                        # update MODE
                        -m=* | --mode=* )
                                MODE="${OPT#*=}"
                                shift
                                ;;
                        -m* | --mode )
                                MODE="$2"
                                shift
                                ;;
                        # update MODE
                        -e=* | --entrypoint=* )
                                MODE_ENTRYPOINT="${OPT#*=}"
                                shift
                                ;;
                        -e* | --entrypoint )
                                MODE_ENTRYPOINT="$2"
                                shift
                                ;;
                        # update JUPYTER_PORT
                        -p=* | --port=* )
                                JUPYTER_PORT="${OPT#*=}"
                                shift
                                ;;
                        -p* | --port )
                                JUPYTER_PORT="$2"
                                shift
                                ;;
                        # set CONFIG_FILE
                        -f=* | --file=* )
                                CONFIG_FILE="${OPT#*=}"
                                shift
                                ;;
                        -f* | --file )
                                CONFIG_FILE="$2"
                                shift
                                ;;
                        -o=* | --output=* )
                                OUTPUT_FOLDER="${OPT#*=}"
                                shift
                                ;;
                        -o* | --output )
                                OUTPUT_FOLDER="$2"
                                shift
                                ;;
                        --server=* )
                                GALAXY_SERVER="${OPT#*=}"
                                shift
                                ;;
                        --server )
                                GALAXY_SERVER="$2"
                                shift
                                ;;
                        --api-key=* )
                                GALAXY_API_KEY="${OPT#*=}"
                                shift
                                ;;
                        --api-key )
                                GALAXY_API_KEY="$2"
                                shift
                                ;;
                        --enable-logger )
                                ENABLE_LOGGER="--enable-logger"
                                ;;
                        --disable-cleanup )
                                DISABLE_CLEANUP="--disable-cleanup"
                                ;;
                        --debug )
                                ENABLE_DEBUG="--debug"
                                ;;
                        -h* | --help )
                                print_usage
                                exit
                                ;;

                        # Anything unknown is recorded for later
                        * )
                                DOCKER_OPTS="$DOCKER_OPTS $OPT"
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

# check MODE
if [[ ! ${MODE} =~ ^(production|develop)$ ]]; then
  echo -e "\nInvalid mode parameter: ${MODE} !!!"
  print_usage
  exit
fi

# set default MODE_ENTRYPOINT
if [[ -z ${MODE_ENTRYPOINT} ]]; then
  if [[ ${MODE} == "production" ]]; then
    MODE_ENTRYPOINT="wft4galaxy"
  else
    MODE_ENTRYPOINT="bash"
  fi
else
  if [[ ((${MODE} == "production") && (! ${MODE_ENTRYPOINT} =~ ^(bash|wft4galaxy)$ )) || \
        ((${MODE} == "develop") && (! ${MODE_ENTRYPOINT} =~ ^(bash|wft4galaxy|ipython|jupyter)$ )) ]]
  then
    echo -e "\nInvalid MODE_ENTRYPOINT: '${MODE_ENTRYPOINT}' for MODE '${MODE}'"
    print_usage
    exit
  fi
fi

# udpate DOCKER image
if [[ ${MODE} == "production" ]]; then
  DOCKER_IMAGE="${DOCKER_REGISTRY}/wft4galaxy:${BASE_OS}"
else
  DOCKER_IMAGE="${DOCKER_REGISTRY}/wft4galaxy-dev:${BASE_OS}"
fi


# print debug message
if [[ ${ENABLE_DEBUG} == "--debug" ]]; then
    echo "MODE:             ${MODE}"
    echo "MODE ENTRYPOINT:  ${MODE_ENTRYPOINT}"
    echo "GALAXY SERVER:    $GALAXY_SERVER"
    echo "GALAXY API KEY:   $GALAXY_API_KEY"
    echo "CONFIG FILE:      $CONFIG_FILE"
    echo "OUTPUT FOLDER:    $OUTPUT_FOLDER"
    echo "ENABLE_LOGGER:    $ENABLE_LOGGER"
    echo "DISABLE_CLEANUP:  $DISABLE_CLEANUP"
    echo "ENABLE_DEBUG:     $ENABLE_DEBUG"
    echo "DATA INPUT:       $DATA_INPUT"
    echo "DATA OUTPUT:      $DATA_OUTPUT"
    echo "DATA CONFIG FILE: $DATA_CONFIG_FILE"
    echo "DOCKER IMAGE:     $DOCKER_IMAGE"
    echo "DOCKER OPTIONS:   $DOCKER_OPTS"
    echo "JUPYTER PORT:     $JUPYTER_PORT"
fi

if [[ ${MODE_ENTRYPOINT} == "wft4galaxy" ]]; then
  # check required parameters
  if [[ -z ${CONFIG_FILE} ]]; then
  	echo -e "Missing parameter: [-f|--file] "
  fi
  if [[ -z ${OUTPUT_FOLDER} ]]; then
  	echo -e "Missing parameter: [-o|--output]"
  fi
  if [[ (-z ${CONFIG_FILE}) || (-z ${OUTPUT_FOLDER}) ]]; then
  	print_usage
  	exit
  fi

  # set data paths
  DATA_INPUT=$(realpath $(dirname ${CONFIG_FILE}))
  DATA_OUTPUT=$(realpath ${OUTPUT_FOLDER})
  DATA_CONFIG_FILE=/data_input/$(basename ${CONFIG_FILE})

  # run wft4galaxy tests within a docker container
  docker run -it --rm ${DOCKER_OPTS} \
              -v ${DATA_INPUT}:/data_input \
              -v ${DATA_OUTPUT}:/data_output \
              ${DOCKER_IMAGE} ${MODE_ENTRYPOINT} \
              --server ${GALAXY_SERVER} --api-key ${GALAXY_API_KEY} \
              -f ${DATA_CONFIG_FILE} \
              -o /data_output ${ENABLE_LOGGER} ${DISABLE_CLEANUP} ${ENABLE_DEBUG}
elif [[ ${MODE_ENTRYPOINT} == "jupyter" ]]; then
  docker run -it --rm -p ${JUPYTER_PORT}:8888 ${DOCKER_OPTS} ${DOCKER_IMAGE} \
    ${MODE_ENTRYPOINT} --server ${GALAXY_SERVER} --api-key ${GALAXY_API_KEY}
else
  docker run -it --rm ${DOCKER_OPTS} ${DOCKER_IMAGE} \
    ${MODE_ENTRYPOINT} --server ${GALAXY_SERVER} --api-key ${GALAXY_API_KEY}
fi
