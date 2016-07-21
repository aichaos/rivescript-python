all: build

build:
	python setup.py build

install:
	python setup.py install

test:
	pip install -r requirements.txt
	nosetests

clean:
	rm -rf build dist rivescript.egg-info
	find . -name '*.pyc' -delete

.PHONY: build install test clean
