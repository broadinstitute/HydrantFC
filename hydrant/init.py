#! /usr/bin/env python
# encoding: utf-8

"""Template generator for Firecloud WDL + Docker tasks"""

import os
import pwd
from argparse import ArgumentParser, ArgumentTypeError
from WDL import WDL
from collections import namedtuple

UserTaskList = namedtuple('UserTaskList', 'flow tasks')

def new_folder(folder_name):
    if os.path.isdir(folder_name):
        raise ArgumentTypeError("{} already exists".format(folder_name))
    else:
        os.mkdir(folder_name)
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

def generate_task(task):
    ##Make new folders
    os.makedirs(os.path.join(task, "src"))

    ##Paths for contents
    version_path = os.path.join(task, "VERSION")
    dockerfile_path = os.path.join(task, "Dockerfile")
    dockerignore_path = os.path.join(task, ".dockerignore")

    with open(version_path, 'w') as vf:
        ##Start with version 1
        vf.write("1\n")

    with open(dockerfile_path, 'w') as df:
        df.write(dockerfile_contents())

    with open(dockerignore_path, 'w') as di:
        di.write(dockerignore_contents())

def task_wdl_contents(task_num, workflow, fullname, username):
    if task_num == 1:
        contents = '''task task_{tasknum} {{
    Boolean package
    String null_file
    String package_name
    String package_archive="${{package_name}}.zip"
    Int? local_disk_gb
    Int? num_preemptions

    #**Define additional inputs here**

    command {{
        set -euo pipefail

        #**Command goes here**

        if ${{package}}; then
            zip -r ${{package_name}} . -x \\
                "fc-[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]/*" \\
                lost+found/\* \\
                broad-institute-gdac/\* \\
                "tmp.[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]/*" \\
                exec.sh
        fi
    }}

    output {{
        File {workflowname}_pkg="${{if package then package_archive else null_file}}"
        #** Define additional outputs here**
    }}

    runtime {{
        docker : "broadgdac/task_{tasknum}:1"
        disks : "local-disk ${{if defined(local_disk_gb) then local_disk_gb else '10'}} HDD"
        preemptible : "${{if defined(num_preemptions) then num_preemptions else '0'}}"
    }}

    meta {{
        author : "{fullname}"
        email : "{username}@broadinstitute.org"
    }}
}}

'''
    else:
        contents = '''task task_{tasknum} {{
    Boolean package
    String null_file
    File package_archive
    String package_name=basename(package_archive)
    Int? local_disk_gb
    Int? num_preemptions

    #**Define additional inputs here**

    command {{
        set -euo pipefail

        #**Command goes here**

        if ${{package}}; then
            mv ${{package_archive}} .
            zip -r ${{package_name}} . -x \\
                "fc-[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9]-[a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]/*" \\
                lost+found/\* \\
                broad-institute-gdac/\* \\
                "tmp.[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]/*" \\
                exec.sh
        fi
    }}

    output {{
        File {workflowname}_pkg="${{if package then package_name else null_file}}"
        #** Define additional outputs here**
    }}

    runtime {{
        docker : "broadgdac/task_{tasknum}:1"
        disks : "local-disk ${{if defined(local_disk_gb) then local_disk_gb else '10'}} HDD"
        preemptible : "${{if defined(num_preemptions) then num_preemptions else '0'}}"
    }}

    meta {{
        author : "{fullname}"
        email : "{username}@broadinstitute.org"
    }}
}}

'''
    return contents.format(tasknum=task_num, workflowname=workflow,
                           fullname=fullname, username=username)

def workflow_wdl_contents(workflow_name, num_tasks, user_tasks):
    pwuid = pwd.getpwuid(os.getuid())
    all_tasks = ''
    workflow = '''workflow {workflowname} {{
    Boolean package
    String null_file="gs://broad-institute-gdac/GDAC_FC_NULL"
    String package_name="{workflowname}"'''.format(workflowname=workflow_name)
    if user_tasks:
        all_tasks = "\n\n".join(task.text for task in user_tasks) + "\n\n"
        workflow += "\n\n" + "\n\n".join("    call " + task.name
                                         for task in user_tasks)
    for task in range(1, num_tasks + 1):
        all_tasks += task_wdl_contents(task, workflow_name, pwuid[4], pwuid[0])
        if task == 1:
            workflow += '''

    call task_1 {
        input: package=package,
               null_file=null_file,
               package_name=package_name
    }'''
        else:
            workflow += '''

    call task_{tasknum} {{
        input: package=package,
               null_file=null_file,
               package_archive=task_{prevtask}.{workflowname}_pkg
    }}'''.format(tasknum=task, prevtask=task - 1, workflowname=workflow_name)
        if task == num_tasks:
            workflow += '''

    output {{
        task_{tasknum}.{workflowname}_pkg
    }}
}}
'''.format(tasknum=task, workflowname=workflow_name)
    if num_tasks < 1:
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

def generate_workflow(workflow, num_tasks, user_tasks):    
    # Make new folders
    # task folders
    for task in range(1, num_tasks + 1):
        task_folder = os.path.join(workflow, 'task_%d' % task)
        generate_task(task_folder)
    
    # test folder
    os.mkdir(os.path.join(workflow, "tests"))

    wdl_path = os.path.join(workflow, workflow + ".wdl")
    with open(wdl_path, 'w') as wf:
        wf.write(workflow_wdl_contents(workflow, num_tasks, user_tasks))

def main(args=None):
    parser = ArgumentParser(description="Template generator for " +
                            "FireCloud tasks and workflows")
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    parser.add_argument('-n', '--num_tasks', type=int, default=1,
                        help='Number of empty tasks to create')
    parser.add_argument('workflow', type=new_folder,
                        help='Name of template folder')
    parser.add_argument('task', nargs='*', type=user_task,
                        help='Name of existing locally written task to ' +
                             'initialize with in the format of ' +
                             '<workflow>.<task|*>, with "<workflow>.*" ' +
                             'indicating all tasks in <workflow>')
    
    args = parser.parse_args(args)
    user_tasks = process_user_tasks(args.task, args.workflow)
    generate_workflow(args.workflow, args.num_tasks, user_tasks)

if __name__ == '__main__':
    main()
