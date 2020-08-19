#!/bin/bash
make
for i in {1..1000}; do
	echo "=== test#$i ==="
	if ! ./a.out > /dev/null; then
		echo "exits with error $? at test#$i"
		exit
	fi
done
echo "pass all tests."
