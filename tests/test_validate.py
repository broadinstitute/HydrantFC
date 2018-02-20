# encoding: utf-8

import pytest
from hydrant import validate

def test_main_no_wdl():
    with pytest.raises(SystemExit) as excinfo:
        validate.main()
    assert str(excinfo.value) == '2'
