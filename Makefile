.PHONY: all
all: build

.PHONY: build
build:
	python setup.py build

.PHONY: install
install:
	python setup.py install

.PHONY: test
test:
	pip install -r requirements.txt
	nosetests

.PHONY: clean
clean:
	rm -rf build dist rivescript.egg-info
	find . -name '*.pyc' -delete

.PHONY: rpm
rpm:
	./docker/build.sh

.PHONY: docker.rpm
docker.rpm:
	./docker/package.sh
