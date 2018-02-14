#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from json import load as json_load
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

    # Validate JSON syntax before incurring cost of launching Cromwell
    try:
        _ = json_load(open(inputs_json))
    except Exception as e:
        (exc_type, exc_value) = sys.exc_info()[:2]
        logging.error("validating JSON %s:\n\t%s (%s)" % \
                        (inputs_json, exc_type.__name__, exc_value))
        sys.exit(3)

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
