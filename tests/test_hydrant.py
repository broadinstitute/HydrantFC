# encoding: utf-8
import pytest
from hydrant import hydrant

def test_main():
    with pytest.raises(SystemExit) as excinfo:
        hydrant.main()
    assert str(excinfo.value) == '0'