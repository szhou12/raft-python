#!/bin/bash

TIMES=$1
FILE=$2

failures=0

for ((i=1; i<=TIMES; i++))
do
    echo "Running test $i/$TIMES"
    pytest $FILE
    if [ $? -ne 0 ]; then
        echo "Test failed on run $i"
        failures=$((failures + 1))
    fi
done

echo "Test failure rate: $failures / $TIMES"