#!/bin/bash

if [[ ! -f "./python-rivescript.spec" ]]; then
    cd ..
    if [[ ! -f "./python-rivescript.spec" ]]; then
        echo Could not find the python-rivescript.spec; are you in the right folder?
        exit 1
    fi
fi

mkdir -p ./docker/dist

sudo docker build -t rivescript_fedora -f ./docker/Fedora.dockerfile .
sudo docker run --rm -v "$(pwd)/docker/dist:/mnt/export:z" rivescript_fedora
