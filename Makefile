
install:
	pip2 install --upgrade .

sinstall:
	sudo -H pip2 install --upgrade .

test:
	python2 setup.py test
	
clean:
	$(RM) *~ *.pyc
	$(RM) -rf .eggs *.egg-info tests/__pycache__ .pytest_cache
