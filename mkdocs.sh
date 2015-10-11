#!/bin/bash

rm -rf docs/*
epydoc -v -o docs --name RiveScript --url https://github.com/aichaos/rivescript-python rivescript.rivescript rivescript.python
