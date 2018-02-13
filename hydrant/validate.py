#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from subprocess import check_call, check_output
from util import ArgumentParser, find_tool
from ConfigLoader import ConfigLoader

Description = "Verify syntax of WDL workflow and generate test json"

def validate(wdl=None, inputs_json='tests/inputs.json'):

    if not wdl:
        wdl = os.path.basename(os.getcwd()) + ".wdl"
    if not os.path.exists(wdl):
        logging.exception("WDL not found: " + wdl)
        sys.exit(2)
    config = ConfigLoader().config.All
    WDLTOOL = find_tool(config.WDLtool, "wdltool")
    inputs_json_bak = None
    try:
        check_call(['java', '-jar', WDLTOOL, 'validate', wdl])
        if os.path.exists(inputs_json):
            inputs_json_bak = inputs_json + '.bak'
            os.rename(inputs_json, inputs_json_bak)
        with open(inputs_json, 'w') as inputs:
            logging.info('Writing %s', inputs_json)
            input_data = check_output(['java', '-jar', WDLTOOL, 'inputs', wdl],
                                      universal_newlines=True).strip().split('\n')
            # Sort inputs with workflow inputs first, then task inputs 
            input_data[1:-1] = sorted(input_data[1:-1],
                                      key=lambda x: "{}{}".format(x.split(':')[0].count('.'), x))
            for datum in input_data:
                inputs.write(datum + '\n')
    except:
        if inputs_json_bak is not None:
            os.rename(inputs_json_bak, inputs_json)
        logging.exception("Unable to validate %s", wdl)
        sys.exit(1)

def main(args=None):
    parser = ArgumentParser(description=Description)
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    
    args = parser.parse_args(args)
    validate()

if __name__ == '__main__':
    main()
