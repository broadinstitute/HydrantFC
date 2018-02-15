
install:
	pip install --upgrade .

test:
	python setup.py test
	
clean:
	$(RM) *~ *.pyc
