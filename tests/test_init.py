# encoding: utf-8

import pytest
import os
from hydrant import init
from hydrant.ConfigLoader import ConfigLoader
from hydrant.WDL import WDL


def test_main():
    with pytest.raises(SystemExit) as excinfo:
        init.main()
    assert str(excinfo.value) == '0'
    
def test_cli_cfg(workflows_dir):
    with workflows_dir.as_cwd():
        flow_name = 'CLIcfgTest'
        init.main(['-c', 'cli.cfg', flow_name])
        task_cfgs = ConfigLoader(cli_cfg='cli.cfg').config.Tasks
        # Confirm generation of workflow directory
        assert os.path.isdir(flow_name)
        # Confirm generation of WDL
        wdl_file = os.path.join(flow_name, flow_name) + '.wdl'
        assert os.path.isfile(wdl_file)
        # Confirm generation of generic task directory
        generic_task = '{}_task_{}'.format(flow_name.lower(), 1)
        assert os.path.isdir(os.path.join(flow_name, generic_task))
        # Confirm presence of task entry in WDL
        wdl_obj = WDL(wdl_file)
        assert generic_task in wdl_obj.tasks
        # Confirm generation of custom task directories and respective configs
        for task in task_cfgs._fields:
            # Confirm presence of task entry in WDL
            assert task in wdl_obj.tasks
            taskdir = os.path.join(flow_name, task)
            assert os.path.isdir(taskdir)
            docker_cfg = ConfigLoader(taskdir).config.Docker
            task_cfg = getattr(task_cfgs, task)
            for field in docker_cfg._fields:
                assert getattr(docker_cfg, field) == getattr(task_cfg, field)
