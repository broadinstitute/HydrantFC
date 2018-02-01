#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from subprocess import check_call, check_output
from argparse import ArgumentParser
from pkg_resources import resource_filename

from collections import namedtuple
from six.moves.urllib.request import urlretrieve

from init import main as init
from build import main as build
from publish import main as publish
from install import main as install
from __about__ import __version__

Config = namedtuple('Config',
                    'HYDRANTBIN CROMWELL_RELEASE WDLTOOL_RELEASE UTILS')

def validate_util(hydrantbin, url, name):
    local = os.path.join(hydrantbin, url.rsplit('/', 1)[-1])
    if not os.path.exists(hydrantbin):
        logging.warn("No path found for hydrant utilities, creating %s",
                     hydrantbin)
        os.mkdir(hydrantbin)
    if not os.path.exists(local):
        logging.warn("%s not found. Downloading from %s to %s.",
                     name, url, local)
        urlretrieve(url, local)
    return local

def validate(config, wdl, inputs_json='tests/inputs.json'):
    WDLTOOL = validate_util(config.HYDRANTBIN, config.WDLTOOL_RELEASE,
                            "wdltool")
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

def test(config, wdl, inputs_json='tests/inputs.json'):
    runcromw = os.path.join(config.UTILS, 'runcromw.sh')
    CROMWELL = validate_util(config.HYDRANTBIN, config.CROMWELL_RELEASE,
                             "Command-line cromwell")
    try:
        check_call([runcromw, CROMWELL, wdl, inputs_json])
    except:
        logging.exception('Workflow test failed')
        sys.exit(1)

def config():
    pass

def main(args=None):
    defaults = Config(
        HYDRANTBIN = os.path.expanduser(os.path.join("~", ".hydrant")),
        CROMWELL_RELEASE = "https://github.com/broadinstitute/cromwell/" +
                           "releases/download/30.2/cromwell-30.2.jar",
        WDLTOOL_RELEASE  = "https://github.com/broadinstitute/cromwell/" +
                           "releases/download/30.2/womtool-30.2.jar",
        UTILS            = resource_filename(__name__, 'util')
        )
    
    parser = ArgumentParser(description="Hydrant: A tool for installing " +
                                        "workflows into FireCloud")
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    subparsers = parser.add_subparsers(dest='subcmd')
    subparsers.add_parser('init', help="Create a directory tree under the " +
                          "current one with structure and templates to " +
                          "facilitate building a FireCloud workflow or a " +
                          "docker image for use in one", add_help=False)
    subparsers.add_parser('build', help="Build the docker image defined in " +
                          "the local Dockerfile", add_help=False)
    subparsers.add_parser('publish', help="Push the docker image to dockerhub",
                          add_help=False)
    subparsers.add_parser('sync', help="Update the WDLs of all local " +
                          "workflows using this docker image to the latest " +
                          "version")
    subparsers.add_parser('validate', help="Run wdltool to validate the WDL " +
                          "and generate initial inputs.json")
    subparsers.add_parser('test', help="Run command-line cromwell to test " +
                          "the workflow defined in the WDL with test data " +
                          "specified in inputs.json")
    subparsers.add_parser('install', add_help=False,
                          help="Push WDL to your FireCloud method repository")
    subparsers.add_parser('config', help="Update workspace task configs " +
                          "with the latest snapshot you have committed")
    
    args, opts = parser.parse_known_args(args)
    
    # TODO: Build a dict of hydrant arguments with values being the function to
    #       call, it will make the below a lot cleaner.
    wdl = os.path.basename(os.getcwd()) + ".wdl"
    if args.subcmd == 'init':
        init(opts)
    elif args.subcmd == 'validate':
        validate(defaults, wdl)
    elif args.subcmd == 'test':
        test(defaults, wdl)
    elif args.subcmd == 'install':
        install(opts)
    elif args.subcmd == 'build':
        build(opts)
    elif args.subcmd == 'publish':
        publish(opts)
    
if __name__ == '__main__':
    main()
