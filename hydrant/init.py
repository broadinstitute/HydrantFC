#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import pwd
from argparse import ArgumentTypeError
from WDL import WDL
from collections import namedtuple
from shutil import copy2 as cp, copytree as copydir
from util import ArgumentParser, FIXEDPATHS, initialize_logging
from ConfigLoader import ConfigLoader, SafeConfigParser, DockerSection

sys.path.append(FIXEDPATHS.USERDIR)
import templates  # @UnresolvedImport

Description = "Create dir & templates for authoring tasks & workflows"
UserTaskList = namedtuple('UserTaskList', 'flow tasks')

def new_folder(folder_name):
    if os.path.isdir(folder_name):
        raise ArgumentTypeError("{} already exists".format(folder_name))
    else:
        os.mkdir(folder_name)
        cp(os.path.join(FIXEDPATHS.DEFAULTS, 'workflow.cfg'),
           os.path.join(folder_name, 'hydrant.cfg'))
        return folder_name

def user_task(flow_task):
    try:
        flow, task = flow_task.split('.')
    except ValueError:
        raise ArgumentTypeError("{} is not in expected ".format(flow_task) +
                                "format of <workflow>.<task|*>")
    flow_path = os.path.join(os.getcwd(), flow, flow + '.wdl')
    if not os.path.exists(flow_path):
        raise ArgumentTypeError("Unable to locate {}".format(flow_path))
    wdl = WDL(flow_path)
    
    if task == '*':
        return UserTaskList(flow, wdl.tasks.values())
    
    if task in wdl.tasks:
        return UserTaskList(flow, [wdl.tasks[task]])
    
    raise ArgumentTypeError("Unable to locate {} in {}".format(task, flow))

def task_config(cli_cfg):
    if not os.path.isfile(cli_cfg):
        raise ArgumentTypeError("Unable to locate {}".format(cli_cfg))
    return ConfigLoader(cli_cfg=cli_cfg).config

def process_user_tasks(user_tasks, new_flow):
    # Update/create SYNC files
    processed_tasks = []
    for task_list in user_tasks:
        for task in task_list.tasks:
            processed_tasks.append(task)
            task_path = os.path.join(os.getcwd(), task_list.flow, task.name)
            if os.path.isdir(task_path):
                with open(os.path.join(task_path, 'SYNC'), 'a') as sync:
                    sync.write(new_flow + "\n")
    
    # Return flattened list of tasks
    return processed_tasks

def generate_task(task, pkg, task_cfg=None):
    ##Make new folders
    srcdir = os.path.join(task, "src")
    base_task_cfg = os.path.join(FIXEDPATHS.DEFAULTS, 'task.cfg')
    out_task_cfg = os.path.join(task, 'hydrant.cfg')
    
    if task_cfg is None:
        ##Copy default config
        os.makedirs(srcdir)
        cp(base_task_cfg, out_task_cfg)
    else:
        # TODO: also handle URLs
        if task_cfg.Src is not None:
            if os.path.isdir(task_cfg.Src):
                copydir(task_cfg.Src, srcdir)
            else:
                os.makedirs(srcdir)
                cp(task_cfg.Src, srcdir)
        else:
            os.makedirs(srcdir)
        cfg = SafeConfigParser(allow_no_value=True)
        cfg.optionxform = str
        cfg.read(base_task_cfg)
        for option in DockerSection._fields:
            usr_val = getattr(task_cfg, option)
            if usr_val is not None:
                cfg.set('Docker', option, usr_val)
        with open(out_task_cfg, 'wb') as task_cfg_file:
            cfg.write(task_cfg_file)
            
    
    ##Copy packaging utility
    if pkg:
        cp(os.path.join(FIXEDPATHS.BIN, 'package.sh'), srcdir)  # @UndefinedVariable

    ##Paths for contents
    dockerfile_path = os.path.join(task, "Dockerfile")
    dockerignore_path = os.path.join(task, ".dockerignore")

    with open(dockerfile_path, 'w') as df:
        df.write(dockerfile_contents())

    with open(dockerignore_path, 'w') as di:
        di.write(dockerignore_contents())

def task_wdl_contents(task_name, task_num, workflow, fullname, username,
                      config, pkg):
    tag = 1
    namespace = config.Docker.Namespace
    if config.Tasks is not None:
        task_cfg = getattr(config.Tasks, task_name, None)
        if task_cfg is not None:
            tag = task_cfg.Tag or tag
            namespace = task_cfg.Namespace or namespace
    if task_num == 1:
        contents = templates.task_1_wdl_pkg if pkg else templates.task_1_wdl
    else:
        contents = templates.task_n_wdl_pkg if pkg else templates.task_n_wdl
    
    return contents.safe_substitute(task=task_name, workflowname=workflow,
                                    fullname=fullname, username=username,
                                    tag=tag,
                                    namespace=namespace or '<namespace>')

def workflow_wdl_calls(task_name, task_num, workflow, tot_tasks, prev_task, pkg):
    if task_num == 1:
        workflow_wdl = templates.call_task_1_wdl_pkg if pkg else \
                       templates.call_task_1_wdl
        workflow_wdl = workflow_wdl.safe_substitute(task=task_name)
    else:
        workflow_wdl = templates.call_task_n_wdl_pkg if pkg else \
                       templates.call_task_n_wdl
        workflow_wdl = workflow_wdl.safe_substitute(task=task_name,
                                                    prevtask=prev_task,
                                                    workflowname=workflow)
    if task_num == tot_tasks:
        wf_wdl_end = templates.workflow_wdl_end_pkg if pkg else \
                     templates.workflow_wdl_end
        workflow_wdl += wf_wdl_end.safe_substitute(task=task_name,
                                                   workflowname=workflow)
    
    return workflow_wdl
    

def workflow_wdl_contents(workflow_name, num_tasks, user_tasks, config, pkg):
    pwuid = pwd.getpwuid(os.getuid())
    all_tasks = ''
    wf_wdl_start = templates.workflow_wdl_start_pkg if pkg else \
                   templates.workflow_wdl_start
    workflow = wf_wdl_start.safe_substitute(workflow=workflow_name,
                                            workflowname=workflow_name.lower())
    if user_tasks:
        all_tasks = "\n\n".join(task.text for task in user_tasks) + "\n\n"
        workflow += "\n\n" + "\n\n".join("    call " + task.name
                                         for task in user_tasks)
    tot_tasks = num_tasks
    cfg_task_ct = 0
    task = 0
    prev_task = ''
    if config.Tasks is not None:
        cfg_task_ct = len(config.Tasks)
        tot_tasks += cfg_task_ct
        for tasknum, taskname in enumerate(config.Tasks._fields, 1):
            all_tasks += task_wdl_contents(taskname, tasknum,
                                           workflow_name.lower(), pwuid[4],
                                           pwuid[0], config, pkg)
            workflow += workflow_wdl_calls(taskname, tasknum,
                                           workflow_name.lower(), tot_tasks,
                                           prev_task, pkg)
            prev_task = taskname
    
    for tasknum in range(1, num_tasks + 1):
        task_ct = tasknum + cfg_task_ct
        taskname = '{}_task_{}'.format(workflow_name.lower(), tasknum)
        all_tasks += task_wdl_contents(taskname, task_ct,
                                       workflow_name.lower(), pwuid[4],
                                       pwuid[0], config, pkg)
        workflow += workflow_wdl_calls(taskname, task_ct, workflow_name.lower(),
                                       tot_tasks, prev_task, pkg)
        prev_task = taskname
    if tot_tasks < 1:
        workflow += '\n}'
    return all_tasks + workflow

def dockerfile_contents():
    contents = '''FROM broadgdac/run-r:3.3.2

# Install any libraries necessary to run the task
# RUN set -ex \\
#     && apt-get update \\
#     && apt-get install -y --no-install-recommends \\
#         libcairo2-dev \\
#         libxt-dev \\
#     && rm -rf /var/lib/apt/lists/* \\
#     && install2.r -e \\
#         Cairo \\
#         data.table \\
#     && rm -rf /tmp/*

# Copy the built tool and any supporting files into the image
COPY src /src

# Set the working directory
WORKDIR src
'''
    return contents

def dockerignore_contents():
    return '''*
!src
!Dockerfile
'''

def generate_workflow(workflow, num_tasks, user_tasks, config, pkg):    
    # Make new folders
    # task folders
    for task in range(1, num_tasks + 1):
        task_folder = os.path.join(workflow,
                                   '{}_task_{}'.format(workflow.lower(), task))
        generate_task(task_folder, pkg)
    
    if config.Tasks is not None:
        for task in config.Tasks._fields:
            task_folder = os.path.join(workflow, task)
            generate_task(task_folder, pkg, getattr(config.Tasks, task))
    # test folder
    os.mkdir(os.path.join(workflow, "tests"))

    wdl_path = os.path.join(workflow, workflow + ".wdl")
    with open(wdl_path, 'w') as wf:
        wf.write(workflow_wdl_contents(workflow, num_tasks, user_tasks, config,
                                       pkg))

def main(args=None):

    parser = ArgumentParser(description=Description)

    # Because parser.prog is initialized to the name of the top-level calling
    # module, it needs to be modified here to be consistent.
    # (i.e. so hydrant init -h returns a usage that begins with hydrant init
    # rather than only hydrant)
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]

    parser.add_argument('-p', '--package', action='store_true',
                        help='include packaging tools')
    parser.add_argument('-n', '--num_tasks', type=int, default=1,
                        help='Number of empty tasks to create')
    parser.add_argument('-c', '--config', type=task_config,
                        help='Config file with [Task <task_name>] sections ' +
                             'that may contain Src=<path/to/src> and ' +
                             'any [Docker] section arguments to initialize ' +
                             'tasks with specified names, copy source code ' +
                             "to each task's src directory, and initialize " +
                             "each task's hydrant.cfg")
    parser.add_argument('workflow', type=new_folder,
                        help='Name of template folder')
    parser.add_argument('task', nargs='*', type=user_task,
                        help='Name of existing locally written task to ' +
                             'initialize with in the format of ' +
                             '<workflow>.<task|*>, with "<workflow>.*" ' +
                             'indicating all tasks in <workflow>')
    
    args = parser.parse_args(args)
    user_tasks = process_user_tasks(args.task, args.workflow)
    generate_workflow(args.workflow, args.num_tasks, user_tasks,
                      args.config or ConfigLoader().config, args.package)

if __name__ == '__main__':
    initialize_logging()
    main()
