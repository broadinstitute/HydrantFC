# encoding: utf-8
import pytest
from hydrant import hydrant

def test_main():
    with pytest.raises(SystemExit) as excinfo:
        hydrant.main()
    assert str(excinfo.value) == '0'

@pytest.fixture(scope='module',
                params=['init', 'validate', 'build', 'push', 'test', 'install'])
def hydrant_func(request):
    return request.param

def test_help(hydrant_func):
    with pytest.raises(SystemExit) as excinfo:
        hydrant.main([hydrant_func, '-h'])
    assert str(excinfo.value) == '0'
