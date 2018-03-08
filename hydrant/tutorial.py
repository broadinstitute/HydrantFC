
Description = "Show general flow of hydrant use cases, by example"

import pydoc
import sys

def main(argv=None):
    examples = '''
Hydrant aims to simplify and accelerate the development and maintenance of
workflows for FireCloud.

FireCloud aims to provide a global infrastructure for collaborative,
extreme-scale biomedical analysis and data sharing.

Hydrant is important because FireCloud brings together a substantial range
of related technologies; and for typical researchers, many of whom may not
be software engineers or computer scientists, the complexity of learning and
effectively utilizing this technology stack can be a daunting barrier to
achieving their main goal:

        sharing and exploring research data, and running scienitfic
        codes upon that data, at scale.


The general process of using hydrant to migrate a code to FC looks like

 Hydrant Cmd    Purpose + Followup Manual Steps (denoted by *)
 -----------    -------------------------------------------------------------
    init        Generate a workflow directory tree, with templatized WDL
                        * copy/edit source code into task/src directory (ies)
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

To see how these commands work together in practice, look in the ./tests
subdirectory for examples.  A flowchart and documentation is available at

                https://github.com/broadinstitute/HydrantFC
'''
    return pydoc.pager(examples)

if __name__ == "__main__":
    sys.exit(main())
