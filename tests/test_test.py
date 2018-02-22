# encoding: utf-8

import pytest
from hydrant import test

def test_main():
    with pytest.raises(SystemExit) as excinfo:
        test.main()
    assert str(excinfo.value) == '2'

def test_valid_smoketest(workflows_dir):
    with workflows_dir.join('smoketest').as_cwd():
        test.main()