test:
	flake8 thumbs --ignore=E501,E128
	coverage run --branch --source=periscope nose
	coverage report --omit=test* -m

.PHONY: test