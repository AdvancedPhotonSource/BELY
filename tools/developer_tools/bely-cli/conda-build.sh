#!/bin/bash

ENV_NAME=bely-cli-env
CONDA_DIR=$CONDA_PREFIX_1
echo $CONDA_DIR

if [ -z $CONDA_DIR ]
then
    CONDA_DIR=$CONDA_PREFIX
fi

if [ -z $CONDA_DIR ]
then
    echo '$CONDA_PRIFX must be defined.'
    exit 1
fi

source $CONDA_DIR/etc/profile.d/conda.sh || exit 1

# Clean and Build
rm -rf ./build

# Build API
conda build conda-recipe --output-folder ./build || exit 1

# Install build into a new env
conda create -n $ENV_NAME -y || exit 1
conda activate $ENV_NAME || exit 1
conda install bely-cli -c ./build -y || exit 1

# Export
conda list -n $ENV_NAME --explicit > $ENV_NAME.txt


conda activate
conda env remove -n $ENV_NAME

echo "Please use the c2 tool to upload the $ENV_NAME.txt"
