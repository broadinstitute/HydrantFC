# encoding: utf-8
'''
Templates for generating WDL sections.
Edit for individual use cases. If this file is deleted or renamed, it will be
regenerated the next time hydrant is run.
Keywords:
  task         = Name of task
  prevtask     = Name of previous task
                 (only available in call_task_n_wdl templates)
  workflowname = Name of workflow in lowercase
  workflow     = Name of workflow given on command-line
                 (only in workflow_wdl templates)
  fullname     = Full name of user (only works on unix-based systems)
  username     = Username on system (only works on unix-based systems)
  namespace    = Docker namespace (can be predefined via CLI or global config)
  tag          = Docker image tag (can be predefined via CLI config)
See https://docs.python.org/3/tutorial/stdlib2.html#templating
'''

from string import Template

#=============================================================================#
#                             Packaging templates                             #
#=============================================================================#
# Available keyword(s):
#   task
#   workflowname
#   namespace
#   tag
#   fullname
#   username
task_1_wdl_pkg = Template('''task $task {
    Boolean package
    String null_file
    String package_name
    String package_archive="$${package_name}.zip"
    Int? local_disk_gb
    Int? num_preemptions

    #**Define additional inputs here**

    command {
        set -euo pipefail

        #**Command goes here**

        if $${package}; then
            /src/package.sh -x broad-institute-gdac/\* $${package_name}
        fi
    }

    output {
        File ${workflowname}_pkg="$${if package then package_archive else null_file}"
        #** Define additional outputs here**
    }

    runtime {
        docker : "$namespace/$task:$tag"
        disks : "local-disk $${if defined(local_disk_gb) then local_disk_gb else '10'} HDD"
        preemptible : "$${if defined(num_preemptions) then num_preemptions else '0'}"
    }

    meta {
        author : "$fullname"
        email : "$username@broadinstitute.org"
    }
}

''')

# Available keyword(s):
#   task
#   workflowname
#   namespace
#   tag
#   fullname
#   username
task_n_wdl_pkg = Template('''task $task {
    Boolean package
    String null_file
    File package_archive
    String package_name=basename(package_archive)
    Int? local_disk_gb
    Int? num_preemptions

    #**Define additional inputs here**

    command {
        set -euo pipefail

        #**Command goes here**

        if $${package}; then
            mv $${package_archive} .
            /src/package.sh -x broad-institute-gdac/\* $${package_name}
        fi
    }

    output {
        File ${workflowname}_pkg="$${if package then package_name else null_file}"
        #** Define additional outputs here**
    }

    runtime {
        docker : "$namespace/$task:$tag"
        disks : "local-disk $${if defined(local_disk_gb) then local_disk_gb else '10'} HDD"
        preemptible : "$${if defined(num_preemptions) then num_preemptions else '0'}"
    }

    meta {
        author : "$fullname"
        email : "$username@broadinstitute.org"
    }
}

''')

# Available keyword(s):
#   workflow
#   workflowname
workflow_wdl_start_pkg = Template('''workflow $workflow {
    Boolean package
    String null_file="gs://broad-institute-gdac/GDAC_FC_NULL"
    String package_name="$workflowname"''')

# Available keyword(s):
#   task
call_task_1_wdl_pkg = Template('''

    call $task {
        input: package=package,
               null_file=null_file,
               package_name=package_name
    }''')

# Available keyword(s):
#   task
#   prevtask
#   workflowname
call_task_n_wdl_pkg = Template('''

    call $task {
        input: package=package,
               null_file=null_file,
               package_archive=$prevtask.${workflowname}_pkg
    }''')

# Available keyword(s):
#   task
#   workflowname
workflow_wdl_end_pkg = Template('''

    output {
        $task.${workflowname}_pkg
    }
}
''')

#=============================================================================#
#                           Non-Packaging templates                           #
#=============================================================================#
# Available keyword(s):
#   task
#   workflowname
#   namespace
#   tag
#   fullname
#   username
task_1_wdl = Template('''task $task {
    Int? local_disk_gb
    Int? num_preemptions

    #**Define additional inputs here**

    command {
        set -euo pipefail

        #**Command goes here**
    }

    output {
        #** Define outputs here**
    }

    runtime {
        docker : "$namespace/$task:$tag"
        disks : "local-disk $${if defined(local_disk_gb) then local_disk_gb else '10'} HDD"
        preemptible : "$${if defined(num_preemptions) then num_preemptions else '0'}"
    }

    meta {
        author : "$fullname"
        email : "$username@broadinstitute.org"
    }
}

''')

# Available keyword(s):
#   task
#   workflowname
#   namespace
#   tag
#   fullname
#   username
task_n_wdl = Template('''task $task {
    Int? local_disk_gb
    Int? num_preemptions

    #**Define additional inputs here**

    command {
        set -euo pipefail

        #**Command goes here**
    }

    output {
        #** Define outputs here**
    }

    runtime {
        docker : "$namespace/$task:$tag"
        disks : "local-disk $${if defined(local_disk_gb) then local_disk_gb else '10'} HDD"
        preemptible : "$${if defined(num_preemptions) then num_preemptions else '0'}"
    }

    meta {
        author : "$fullname"
        email : "$username@broadinstitute.org"
    }
}

''')

# Available keyword(s):
#   workflow
#   workflowname
workflow_wdl_start = Template('workflow $workflow {')

# Available keyword(s):
#   task
call_task_1_wdl = Template('''

    call $task {
        input: #**Define call inputs for $task here**
    }''')

# Available keyword(s):
#   task
#   prevtask
#   workflowname
call_task_n_wdl = Template('''

    call $task {
        input: #**Define call inputs for $task here**
    }''')

# Available keyword(s):
#   task
#   workflowname
workflow_wdl_end = Template('''

    output {
        #**Define workflow outputs here. If defined, these will be the only
        #  outputs available in the Method Configuration**
    }
}
''')