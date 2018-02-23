
install:
	pip install --upgrade .

sinstall:
	sudo -H pip install --upgrade .

test:
	python setup.py test
	
clean:
	$(RM) *~ *.pyc
	$(RM) -rf .eggs *.egg-info tests/__pycache__ .pytest_cache
