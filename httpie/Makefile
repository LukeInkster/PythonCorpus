#
# See ./CONTRIBUTING.rst
#

VERSION=$(shell grep __version__ httpie/__init__.py)
REQUIREMENTS="requirements-dev.txt"
TAG="\n\n\033[0;32m\#\#\# "
END=" \#\#\# \033[0m\n"


all: test


init: uninstall-httpie
	@echo $(TAG)Installing dev requirements$(END)
	pip install --upgrade -r $(REQUIREMENTS)

	@echo $(TAG)Installing HTTPie$(END)
	pip install --upgrade --editable .

	@echo


test: init
	@echo $(TAG)Running tests on the current Python interpreter with coverage $(END)
	py.test --cov ./httpie --cov ./tests --doctest-modules --verbose ./httpie ./tests
	@echo


test-tox: init
	@echo $(TAG)Running tests on all Pythons via Tox$(END)
	tox
	@echo


test-dist: test-sdist test-bdist-wheel
	@echo


test-sdist: clean uninstall-httpie
	@echo $(TAG)Testing sdist build an installation$(END)
	python setup.py sdist
	pip install --force-reinstall --upgrade dist/*.gz
	which http
	@echo


test-bdist-wheel: clean uninstall-httpie
	@echo $(TAG)Testing wheel build an installation$(END)
	python setup.py bdist_wheel
	pip install --force-reinstall --upgrade dist/*.whl
	which http
	@echo


# This tests everything, even this Makefile.
test-all: uninstall-all clean init test test-tox test-dist


publish: test-all
	@echo $(TAG)Testing wheel build an installation$(END)
	@echo "$(VERSION)"
	@echo "$(VERSION)" | grep -q "dev"  && echo "!!!Not publishing dev version!!!" && exit 1
	python setup.py register
	python setup.py sdist upload
	python setup.py bdist_wheel upload
	@echo


clean:
	@echo $(TAG)Cleaning up$(END)
	rm -rf .tox *.egg dist build .coverage
	find . -name '__pycache__' -delete -print -o -name '*.pyc' -delete -print
	@echo


uninstall-httpie:
	@echo $(TAG)Uninstalling httpie$(END)
	- pip uninstall --yes httpie &2>/dev/null

	@echo "Verifying…"
	cd .. && ! python -m httpie --version &2>/dev/null

	@echo "Done"
	@echo


uninstall-all: uninstall-httpie

	@echo $(TAG)Uninstalling httpie requirements$(END)
	- pip uninstall --yes pygments requests

	@echo $(TAG)Uninstalling development requirements$(END)
	- pip uninstall --yes -r $(REQUIREMENTS)
