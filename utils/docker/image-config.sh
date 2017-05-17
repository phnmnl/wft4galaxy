#!/usr/bin/env bash

# git info
last_commit=$(git log --format="%H" -n 1)

if [ -z "${git_url}" ]; then
	echo "Getting git repository URL from local repository" >&2
	first_remote=$(git remote | head -n 1)
	echo "Using git remote '${first_remote}'" >&2
	git_url=$(git config --get remote.${first_remote}.url)
fi

if [ -z "${git_branch}" ] ; then
	echo "Git branch not specified.  Using local repository's current branch" >&2
	git_branch=$(git rev-parse --abbrev-ref HEAD)
fi

git_repo_owner=$(echo ${git_url} | sed -E "s/.*[:\/](.*)\/(.*)(\.git)/\1/")
git_repo_name=$(echo ${git_url} | sed -E "s/.*[:\/](.*)\/(.*)(\.git)/\2/")

#replace original repo_url to use the HTTPS protocol
git_url="https://github.com/${git_repo_owner}/${git_repo_name}.git"

# infer image type (minimal|develop) from the containing folder
image_type=$(basename "$(pwd)")

# infer base_os from the containing folder
base_os=$(basename $(dirname "$(pwd)"))

# map the git phnmnl repository to the Crs4 DockerHub repository
if [[ ${git_repo_owner} == "phnmnl" ]]; then
    git_repo_owner="crs4"
fi

# get Docker image tag
tagged_version="false"
docker_tag="${base_os}-${git_branch}"
git_tags=($(git show-ref --tags -s))
for t in ${git_tags[@]}; do
    if [[ ${last_commit} == ${t} ]]; then
        docker_tag=${base_os}-$(git describe --contains ${t})
        tagged_version="true"
        break
    fi
done

# set IMAGE_NAME if not defined
if [[ -z ${IMAGE_NAME} ]]; then
    IMAGE_NAME="${git_repo_owner}/wft4galaxy-${image_type}:${docker_tag}"
fi

# log git/docker info
echo " - Git Repository URL: ${git_url}" >&2
echo " - Last Git commit: ${last_commit}" >&2
echo " - Git branch: ${git_branch}" >&2
echo " - Git owner: ${git_repo_owner}" >&2
echo " - Git repo name: ${git_repo_name}" >&2
echo " - Is tagged version: ${tagged_version}" >&2
echo " - Docker : ${tagged_version}" >&2
echo " - Docker image tag: ${docker_tag}" >&2
echo " - Docker image name: ${IMAGE_NAME}" >&2
