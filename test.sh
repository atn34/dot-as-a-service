#!/bin/bash

set -e

python server.py &
PID=$!

trap "kill -n 1 $PID" EXIT

timeout 10 bash -c "while ! timeout 1 curl localhost:8080/z/health ; do sleep 1 ; done"

[[ $(curl localhost:8080/z/health) == "OK" ]]

python server.py --test
