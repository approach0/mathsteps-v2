#!/bin/bash
make
for i in {1..1000}; do
	if ! ./a.out; then
		echo "exits with error $? at test#$i"
		exit
	fi
done
echo "pass all tests."
