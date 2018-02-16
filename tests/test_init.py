# encoding: utf-8

import pytest
from hydrant import init

def test_main():
    with pytest.raises(SystemExit) as excinfo:
        init.main()
    assert str(excinfo.value) == '0'