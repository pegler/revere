test:
	flake8 revere --ignore=E501,E128
	nosetests --with-coverage --cover-branches --cover-inclusive --cover-package=revere

.PHONY: test