#!/bin/bash

PNAME=$(pwd)/transfer.py
PID=$(ps -ef |grep ${PNAME} |grep -v grep |awk '{print $2}')
[ -z ${PID} ] && exit
kill ${PID}
