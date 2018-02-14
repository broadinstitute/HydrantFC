#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from subprocess import check_call
from util import ArgumentParser, FIXEDPATHS, find_tool, initialize_logging
from ConfigLoader import ConfigLoader

Description = "Run local Cromwell on workflow, with tests/inputs.json"

def test(wdl=None, inputs_json='tests/inputs.json'):
    if not wdl:
        wdl = os.path.basename(os.getcwd()) + ".wdl"
    if not os.path.exists(wdl):
        logging.exception("WDL not found: " + wdl)
        sys.exit(2)
    config = ConfigLoader().config.All
    runcromw = os.path.join(FIXEDPATHS.BIN, 'runcromw.sh')  # @UndefinedVariable
    CROMWELL = find_tool(config.Cromwell, "Command-line cromwell")
    try:
        check_call([runcromw, CROMWELL, wdl, inputs_json])
    except:
        logging.exception('Workflow test failed')
        sys.exit(1)

def main(args=None):
    parser = ArgumentParser(description=Description)
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    
    args = parser.parse_args(args)
    test()

if __name__ == '__main__':
    initialize_logging()
    main()
