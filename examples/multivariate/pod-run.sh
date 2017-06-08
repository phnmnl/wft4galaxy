#!/bin/bash

docker run docker-registry.phenomenal-h2020.eu/phnmnl/multivariate:latest \
	/bin/bash -c mkdir -p working; cd working; /opt/galaxy_data/database/job_working_directory/001/1466/tool_script.sh; return_code=$?; sh -c "exit $return_code"