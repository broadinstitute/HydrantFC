
Description = "Show general flow of hydrant use cases, by example"

import pydoc
import sys

def main(argv=None):
    examples = '''
Hydrant is a tool which aims to simplify and accelerate the development and
maintenance of workflows for FireCloud (FC).  FC aims to provide a global
infrastructure for collaborative, extreme-scale biomedical analysis and data
sharing.  As a cloud computing tool, FC brings together a substantial range
of related technologies, and for typical researchers who may not be software
engineers or computer scientists, the complexity of learning and effectively
utilzing this technology stack can be a daunting barrier to achieving their
main goal: sharing and exploring research data, and running scienitfic codes
upon that data, at scale.

The general process of using hydrant to migrate a code to FC looks like

 Hydrant Cmd    Purpose + Followup Manual Steps (denoted by *)
 -----------    -------------------------------------------------------------
    init        Generate a workflow directory tree, with templatized WDL
                        * copy source code into task/src directory(ies)
                        * edit task/Dockerfile(s)

    build       Fabricate a docker image, using task/src/Dockerfile 

    push        Store this local docker image in the remote Docker repo
                        * edit WDL

    validate    Verify syntax of WDL, and generate JSON test file
                        * edit task/tests/input.json

    test        Run local Cromwell on WDL + docker image, using input.json

    install     Store the local WDL definition in the FC method repository

    config      Create or update workspace method configuration(s), to 
                reference the latest method snapshot installed to the FC
                method repository, edit method parameters, etc

To show how this works in practice let's begin with the simplest case: creating
a FC worfklow that executes a single task, the source code for which is contained
within a single file.

'''
    return pydoc.pager(examples)

if __name__ == "__main__":
    sys.exit(main())