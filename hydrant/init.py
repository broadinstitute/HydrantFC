#! /usr/bin/env python
# encoding: utf-8

"""Template generator for Firecloud WDL + Docker tasks"""

import os
import pwd
from argparse import ArgumentParser, ArgumentTypeError
	
def new_folder(folder_name):
	if os.path.isdir(folder_name):
		raise ArgumentTypeError("{} already exists".format(folder_name))
	else:
		os.mkdir(folder_name)
		return folder_name

def generate_task_folder(foldername, subtask=False):
	##Make new folders
	if not subtask:
		os.mkdir(os.path.join(foldername, "src"))

	##Paths for contents
	version_path = os.path.join(foldername, "VERSION")
	dockerfile_path = os.path.join(foldername, "Dockerfile")

	with open(version_path, 'w') as vf:
		##Start with version 1
		vf.write("1\n")

	with open(dockerfile_path, 'w') as df:
		df.write(dockerfile_contents())

def workflow_wdl_contents(workflow_name):
	pwuid = pwd.getpwuid(os.getuid())
	contents = '''task task_1 {{
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
		docker : "broadgdac/task_1:1"
		disks : "local-disk ${{if defined(local_disk_gb) then local_disk_gb else '10'}} HDD"
		preemptible : "${{if defined(num_preemptions) then num_preemptions else '0'}}"
	}}

	meta {{
		author : "{fullname}"
		email : "{username}@broadinstitute.org"
	}}
}}

task task_n {{
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
		docker : "broadgdac/task_n:1"
		disks : "local-disk ${{if defined(local_disk_gb) then local_disk_gb else '10'}} HDD"
		preemptible : "${{if defined(num_preemptions) then num_preemptions else '0'}}"
	}}

	meta {{
		author : "{fullname}"
		email : "{username}@broadinstitute.org"
	}}
}}

workflow {workflowname} {{
	Boolean package
	String null_file="gs://broad-institute-gdac/GDAC_FC_NULL"
	String package_name="{workflowname}"

	call task_1 {{
		input: package=package,
			   null_file=null_file,
			   package_name=package_name
	}}

	call task_n {{
		input: package=package,
			   null_file=null_file,
			   package_archive=task_1.{workflowname}_pkg
	}}
	
	output {{
		task_n.{workflowname}_pkg
	}}
}}
'''.format(workflowname=workflow_name, fullname=pwuid[4], username=pwuid[0])
	return contents

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

def generate_workflow_folder(foldername):	
	# Make new folders
	# src folder
	src_folder = os.path.join(foldername, "src")
	os.mkdir(src_folder)
	task_1_folder = os.path.join(src_folder, "task_1")
	os.mkdir(task_1_folder)
	generate_task_folder(task_1_folder, True)
	task_n_folder = os.path.join(src_folder, "task_n")
	os.mkdir(task_n_folder)
	generate_task_folder(task_n_folder, True)
	
	# test folder
	os.mkdir(os.path.join(foldername, "tests"))

	wdl_path = os.path.join(foldername, foldername + ".wdl")
	with open(wdl_path, 'w') as wf:
		wf.write(workflow_wdl_contents(foldername))

def main(args=None):
	parser = ArgumentParser(description="Template generator for " +
						    "FireCloud tasks and workflows")
	if __name__ != '__main__':
		parser.prog += " " + __name__.rsplit('.', 1)[-1]
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-t', '--task', action='store_true',
					   help='Create a template task folder')
	group.add_argument('-w', '--workflow', action='store_true',
					   help='Create a template workflow folder')
	parser.add_argument('folder_name', type=new_folder,
					    help='Name of template folder')
	
	args = parser.parse_args(args)
	if args.task:
		generate_task_folder(args.folder_name)
	elif args.workflow:
		generate_workflow_folder(args.folder_name)

if __name__ == '__main__':
	main()
