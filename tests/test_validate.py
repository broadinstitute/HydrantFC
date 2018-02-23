# encoding: utf-8

import pytest
from hydrant import validate
from os import rename

def test_main_no_wdl():
    with pytest.raises(SystemExit) as excinfo:
        validate.main()
    assert str(excinfo.value) == '2'

def test_smoketest_wdl(workflows_dir):
    with workflows_dir.join('smoketest').as_cwd():
        validate.main()
        inputs = workflows_dir.join('smoketest', 'tests', 'inputs.json')
        inputs_bak = workflows_dir.join('smoketest', 'tests', 'inputs.json.bak')
        # ensure all values set in new inputs.json match the old inputs.json
        assert [line.rstrip(',') for line in inputs_bak.readlines(False)] == \
               [line.rstrip(',') for line in inputs.readlines(False) \
                if '(optional) ' not in line]
        inputs_bak.move(inputs)
