
install:
	pip2 install --upgrade .

install3:
	pip3 install --upgrade .

test:
	python2 setup.py test
	
test3:
	python3 setup.py test
	
clean:
	$(RM) *~ *.pyc
	$(RM) -rf .eggs *.egg-info tests/__pycache__ .pytest_cache
