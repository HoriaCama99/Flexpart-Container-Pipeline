#!/bin/bash
# By MB
# Build a FLEXPART container
CPATH=$(dirname $0)
#
# using podman to build containers
#
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT=$(git log --pretty=format:'%h' -n 1)
echo "Building flexpart v11 branch: $BRANCH : $COMMIT"
read -n1 -rsp $'Press any key to continue or Ctrl+C to exit...\n'

cd $CPATH

if [ "$1" != "apptainer" ]; then
    # build with subdirectory as root
    podman build -f Dockerfile -t flexpartv11-${BRANCH}:${COMMIT} --build-arg COMMIT=$COMMIT ../
    # registry
    # podman build -t harbor.wolke.img.univie.ac.at/flexpart/flexpartv11-${BRANCH}:$COMMIT --build-arg COMMIT=$COMMIT ..
else
    apptainer build flexpartv11-${BRANCH}-${COMMIT}.sif Singularity
fi