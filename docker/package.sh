#!/bin/bash

if [[ "x$RIVESCRIPT_DOCKER_BUILD" == "x" ]]; then
    echo This script should only be run from the Docker environment.
    exit 1
fi

if [[ ! -f "./python-rivescript.spec" ]]; then
    cd ..
    if [[ ! -f "./python-rivescript.spec" ]]; then
        echo Could not find the python-rivescript.spec; are you in the right folder?
        exit 1
    fi
fi

# RiveScript module version
VERSION=$(grep -e '__version__' rivescript/__init__.py | head -n 1 | cut -d "'" -f 2)

# Make sure the rpm spec always has this version too.
perl -pi -e "s/^%global version .+?$/%global version ${VERSION}/g" python-rivescript.spec

# Build the tarball and copy everything into the rpmbuild root.
python setup.py sdist
cp dist/*.tar.gz ${HOME}/rpm/
cp python-rivescript.spec ${HOME}/rpm/
echo $(ls -hal dist)
cd ${HOME}/rpm
echo $(ls -hal)

rpmbuild -bb python-rivescript.spec
echo $(ls -hal)
sudo find . -name '*.rpm' -exec cp {} /mnt/export \;
sudo chown 1000:1000 /mnt/export/*.rpm
