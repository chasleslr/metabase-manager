dev:
	@pipenv sync --dev
	@pipenv install -e .
	@pipenv run pre-commit install

release: clear-builds build distribute

clear-builds:
	@rm -rf dist

build: clear-builds
	@pipenv run python setup.py sdist
	@pipenv run setup.py bdist_wheel

distribute:
	@pipenv run twine upload dist/*

distribute-test:
	@pipenv run twine upload --repository testpypi dist/* --verbose
