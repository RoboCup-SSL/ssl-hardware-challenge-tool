#!/usr/bin/sh
protoc -I=protos --python_out=src/ protos/*.proto
echo "Proto files for python generated!"
