#!/bin/bash

# Use this script to build an image with the version of wft4galaxy that's in the
# current project.  This is useful for development.
#

set -o errexit
set -o nounset

function log() {
	echo $@ >&2
}

function usage() {
	log "$(basename $0) [ IMAGE_NAME ]"
}

# work_dir: temporary work directory that will be deleted when the script exits
work_dir=

function cleanup() {
	if [ -n "${work_dir}" ]; then
		log "Cleaning up ${work_dir}"
		rm -rf "${work_dir}"
	fi
}

if [ $# -ne 1 ]; then
	usage
	exit 1
fi

image_name="${1}"

# absolute path of the current script
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
proj_dir="${script_dir}/../../../"

# On exit, for whatever reason, try to clean up
trap "cleanup" EXIT INT ERR

work_dir="$(mktemp -d)"

log "copying project dir to work directory ${work_dir}"
if [ $(ls "${proj_dir}" | grep 'wft4galaxy\|setup.py' | wc -l) -lt 2 ] ; then
	log "There seems to be a problem with the project directory ${proj_dir}"
	log "We're not seeing the expected wft4galaxy directory and the setup.py"
	log "file.  Is something wrong?"
	exit 1
fi

cp -a ${proj_dir}/* "${work_dir}"
cp ${script_dir}/bashrc "${work_dir}"
cp ${script_dir}/*.sh "${work_dir}"

sed_script="${work_dir}/Dockerfile.sed"
# subtle thing: when ADDing multiple things to a directory, the directory's
# path must end with a slash
cat <<END > "${sed_script}"
/git  *clone .*\${WFT4GALAXY/d
/^RUN  *echo  *"Installing dependencies"/i\\
ADD . "\${WFT4GALAXY_PATH}\/"
END

sed -f "${sed_script}" "${proj_dir}/utils/docker/minimal/Dockerfile" > "${work_dir}/Dockerfile"

log "New Dockerfile"
cat "${work_dir}/Dockerfile"

cd "${work_dir}"
docker build -t ${image_name} .

exit 0
