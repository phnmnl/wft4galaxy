#!/bin/bash

# set Docker image
DOCKER_IMAGE="wft4galaxy"

# set defaults
GALAXY_SERVER=${BIOBLEND_GALAXY_URL}
GALAXY_API_KEY=${BIOBLEND_GALAXY_API_KEY}

# print usage
function print_usage(){
    echo -e "Usage: wft4galaxy-docker [options]\n"
    echo -e "    Options:"
    echo -e "\t  -h, --help            show this help message and exit"
    echo -e "\t  --server=SERVER       Galaxy server URL"
    echo -e "\t  --api-key=API_KEY     Galaxy server API KEY"
    echo -e "\t  --enable-logger       Enable log messages"
    echo -e "\t  --debug               Enable debug mode"
    echo -e "\t  --disable-cleanup     Disable cleanup"
    echo -e "\t  -o OUTPUT, --output=OUTPUT"
    echo -e "\t                        absolute path of the folder where output is written"
    echo -e "\t  -f FILE, --file=FILE  YAML configuration file of workflow tests"
}

# parse arguments
while [ -n "$1" ]; do
        # Copy so we can modify it (can't modify $1)
        OPT="$1"
        # Detect argument termination
        if [ x"$OPT" = x"--" ]; then
                shift
                for OPT ; do
                        REMAINS="$REMAINS \"$OPT\""
                done
                break
        fi
        # Parse current opt
        while [ x"$OPT" != x"-" ] ; do
                case "$OPT" in
                        # Handle --flag=value opts like this
                        -c=* | --config=* )
                                CONFIG_FILE="${OPT#*=}"
                                shift
                                ;;
                        # and --flag value opts like this
                        -c* | --config )
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
                                REMAINS="$REMAINS \"$OPT\""
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


# check required parameters
if [[ (-z ${CONFIG_FILE}) && (-z ${OUTPUT_FOLDER}) ]]; then
	echo "missing operands"
	print_usage
	exit
fi

# set data paths
DATA_INPUT=$(realpath $(dirname ${CONFIG_FILE}))
DATA_OUTPUT=$(realpath ${OUTPUT_FOLDER})
DATA_CONFIG_FILE=/data_input/$(basename ${CONFIG_FILE})

# print debug message
if [[ ${ENABLE_DEBUG} == "--debug" ]]; then
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
fi

# run wft4galaxy tests within a docker container
docker run -it --rm \
            -v ${DATA_INPUT}:/data_input \
            -v ${DATA_OUTPUT}:/data_output \
            ${DOCKER_IMAGE} \
            --server ${GALAXY_SERVER} --api-key ${GALAXY_API_KEY} \
            -f ${DATA_CONFIG_FILE} \
            -o /data_output ${ENABLE_LOGGER} ${DISABLE_CLEANUP} ${ENABLE_DEBUG}
