VERSION			:= $(shell git describe --always --dirty)


install:
	python3 -m pip install --upgrade pip
	pip3 install poetry
	poetry install

package:
	poetry version ${VERSION}
	poetry build

publish:
	poetry publish
