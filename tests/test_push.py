# encoding: utf-8

import pytest
from hydrant import push

def test_main():
    with pytest.raises(SystemExit) as excinfo:
        push.main()
    assert str(excinfo.value) == '2'
