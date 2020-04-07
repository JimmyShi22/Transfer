#!/bin/bash
PWD=$(pwd)
[ -z $1 ] && echo "local or vps ?" && exit
nohup python ${PWD}/transfer.py $1 > log.txt 2>&1 &
ps -ef |grep ${PWD}/transfer.py |grep -v grep
echo "Start success!"
