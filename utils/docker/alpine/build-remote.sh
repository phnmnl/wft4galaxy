#!/usr/bin/env bash

function print_usage() {
  (echo "USAGE: $0 [ Repo URL [revision] ]"
   echo
   echo "If no arguments are provided, this script will try to get the"
   echo "required repository information from the local repository itself") >&2
}

if [ $# -gt 4 ]; then
  print_usage
  exit 1
fi

if [ "${1}" == "-h" ]; then
  print_usage
  exit 0
fi

if [ $# -eq 0 ]; then
  printf "== No user specified arguments.  Using defaults from local repository ==\n\n" >&2
fi

if [ $# -eq 2 ]; then
  git_branch="${2}"
  echo " - Using user-specified git revision ${git_branch}"
fi

if [ $# -ge 1 ]; then
  git_url="${1}"
  echo " - Using user-specified git repository url ${git_url}"
fi

# load git/docker info
source "../image-config.sh"

if [ -z "${git_branch}" -o -z "${git_url}" ]; then
  echo "Error fetching remote repository information :-(  Try specifying it on the command line" >&2
  exit 1
fi


# build the Docker image
docker build --build-arg git_branch=${git_branch} --build-arg git_url=${git_url} -t ${IMAGE_NAME} .
