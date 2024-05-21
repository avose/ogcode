#!/usr/bin/env bash

SCRIPT_DIR=$(readlink -f `dirname "$0"`)
export PYTHONPATH=${SCRIPT_DIR}/src:${PYTHONPATH}

python3 -m ogcode
