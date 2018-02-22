# encoding: utf-8

import pytest
from hydrant import build

def test_main():
    with pytest.raises(SystemExit) as excinfo:
        build.main()
    assert str(excinfo.value) == '2'

def test_smoketest_report(workflows_dir):
    with workflows_dir.join('smoketest', 'smoketest_report').as_cwd():
        build.main()
