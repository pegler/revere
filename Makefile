test:
	flake8 periscope --ignore=E501,E128
	nosetests --with-coverage --cover-branches --cover-inclusive --cover-package=periscope

.PHONY: test