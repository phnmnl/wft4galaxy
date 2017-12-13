#!/bin/bash

# Collect arguments to be passed on to the next program in an array, rather than
# a simple string. This choice lets us deal with arguments that contain spaces.
ENTRYPOINT_ARGS=()

# parse arguments
while [ -n "$1" ]; do
    # Copy so we can modify it (can't modify $1)
    OPT="$1"
    # Detect argument termination
    if [ x"$OPT" = x"--" ]; then
            shift
            for OPT ; do
                    # append to array
                    ENTRYPOINT_ARGS+=("$OPT")
            done
            break
    fi
    # Parse current opt
    while [ x"$OPT" != x"-" ] ; do
            case "$OPT" in
              bash | ipython | jupyter | wft4galaxy | runtest | wizard )
                          ENTRYPOINT="$1"
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
                  * )
                          # append to array
                          ENTRYPOINT_ARGS+=("$OPT")
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

# set BIOBLEND
export GALAXY_URL="${GALAXY_SERVER}"
export GALAXY_API_KEY="${GALAXY_API_KEY}"

# export wft4galaxy arguments
export ENTRYPOINT
export ENTRYPOINT_ARGS
