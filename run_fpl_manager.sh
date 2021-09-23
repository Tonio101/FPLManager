#!/bin/bash

FLOCK=/usr/bin/flock
LOCK_FILE=/tmp/fplmanager.lockfile

TOP_DIR=${HOME}/FPLManager
SRC_DIR=${TOP_DIR}/src

source ${TOP_DIR}/.env

SCRIPT=${SRC_DIR}/fpl_main.py
ARGS="--config ${SRC_DIR}/fpl_config_test.json --gameweek --rank"

$FLOCK  --verbose --exclusive $LOCK_FILE --command "$SCRIPT $ARGS"