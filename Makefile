VERSION			:= $(shell git describe --always --dirty)


dev:
	poetry install

package:
	poetry version ${VERSION}
	poetry build

publish:
	poetry publish
