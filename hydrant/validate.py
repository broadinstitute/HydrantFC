#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from io import open
from subprocess import check_call, check_output
from util import ArgumentParser, find_tool, initialize_logging
from ConfigLoader import ConfigLoader
from six import u

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
        logging.info('Success: %s syntax is correct', wdl)
        if os.path.exists(inputs_json):
            inputs_json_bak = inputs_json + '.bak'
            os.rename(inputs_json, inputs_json_bak)
        with open(inputs_json, 'w') as inputs:
            logging.info('Writing %s', inputs_json)
            input_data = [datum.rstrip(',') for datum in \
                          check_output(['java', '-jar', WDLTOOL, 'inputs', wdl],
                                       universal_newlines=True).strip().split('\n')]
            # Sort inputs with workflow inputs first, then task inputs 
            input_data[1:-1] = sorted(input_data[1:-1],
                                      key=lambda x: "{}{}".format(x.split(':')[0].count('.'), x))
            # Store values previously set by the user
            old_data = dict()
            if inputs_json_bak is not None:
                with open(inputs_json_bak, 'r') as old_data_file:
                    wdl_types = ['File', 'String', 'Int', 'Float', 'Boolean',
                                 'Object']
                    for line in old_data_file:
                        clean_line = line.rstrip().rstrip(',')
                        old_datum = clean_line.split(': ')
                        if len(old_datum) == 2:
                            old_value = old_datum[1].strip().strip('"').replace('(optional) ', '').replace('?', '')
                            if old_value not in wdl_types and \
                                old_value.find('[') < 1:
                                old_data[old_datum[0].strip()] = clean_line
            
            no_comma = len(input_data) - 1
            for idx, datum in enumerate(input_data, 1):
                if idx > 1 and idx < no_comma:
                    datum_key = datum.split(': ')[0].strip()
                    # Restore value previously set by user
                    if datum_key in old_data:
                        datum = old_data[datum_key]
                    datum += ','
                    # If using packaging code, turn it on for testing to avoid
                    # cromwell attempting to localize a google bucket file.
                    datum = datum.replace('.package": "Boolean"',
                                          '.package": true')
                inputs.write(u('{}'.format(datum + '\n')))
        logging.info("Now edit %s to reflect input files etc, then run test",
                     inputs_json)
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
    initialize_logging()
    main()
