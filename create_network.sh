#!/bin/bash

lockdir=/tmp/docker-network.lock
check_lock=`mkdir "$lockdir"`
until $check_lock; do sleep 1; done
echo >&2 "successfully acquired lock: $lockdir"
/usr/bin/docker network inspect rest-to-soap-unit-network 2> /dev/null || /usr/bin/docker network create -d bridge rest-to-soap-unit-network
rmdir "$lockdir"