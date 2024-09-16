format:
	black .
	isort .

lint:
	black --check .
	isort --check .
	flake8 --inline-quotes '"'
	pylint $(shell git ls-files '*.py')
	PYTHONPATH=/ mypy --namespace-packages --show-error-codes . --check-untyped-defs --ignore-missing-imports --show-traceback

safety:
	safety check --policy-file .safety-policy.yml


test:
	coverage run -m unittest tests/test_*
	coverage report --fail-under=90
