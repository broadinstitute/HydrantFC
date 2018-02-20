# encoding: utf-8

import pytest
import os
from hydrant import init
from hydrant.ConfigLoader import ConfigLoader


def test_main():
    with pytest.raises(SystemExit) as excinfo:
        init.main()
    assert str(excinfo.value) == '0'
    
def test_cli_cfg(workflows_dir):
    os.chdir(workflows_dir)
    flow_name = 'CLIcfgTest'
    init.main(['-c', 'cli.cfg', flow_name])
    task_cfgs = ConfigLoader(cli_cfg='cli.cfg').config.Tasks
    assert os.path.isdir(flow_name)
    assert os.path.isfile(os.path.join(flow_name, flow_name) + '.wdl')
    for task in task_cfgs._fields:
        taskdir = os.path.join(flow_name, task)
        assert os.path.isdir(taskdir)
        docker_cfg = ConfigLoader(taskdir).config.Docker
        task_cfg = getattr(task_cfgs, task)
        for field in docker_cfg._fields:
            assert getattr(docker_cfg, field) == getattr(task_cfg, field)