#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from shutil import copy2 as cp
from subprocess import check_call, check_output
from pkg_resources import get_distribution
from six.moves.urllib.request import urlretrieve

from init import main as init
from build import main as build
from push import main as push
from install import main as install
from util import ArgumentParser, FIXEDPATHS

from ConfigLoader import ConfigLoader

__version__ = "TESTING"

def load_config(config):
    pass

def first_run():
    logging.info("First run of hydrant, creating %s", FIXEDPATHS.USERDIR)  # @UndefinedVariable
    os.mkdir(FIXEDPATHS.USERDIR)  # @UndefinedVariable
    copy_cfg()

def copy_cfg():
    indent = " " * 30
    user_cfg = os.path.join(FIXEDPATHS.DEFAULTS, 'user.cfg')  # @UndefinedVariable
    hydrant_cfg = os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')  # @UndefinedVariable
    logging.info('Generating initial hydrant.cfg')
    cp(user_cfg, hydrant_cfg)
    logging.info("%s added. You may edit using INI file structure and basic " +
                 "interpolation as defined here:\n%s%s\n%sWorkspaces list " +
                 "may be defined with commas (Workspaces=ws1,ws2,ws3).",
                 hydrant_cfg, indent + "    ",
                 "https://docs.python.org/3/library/configparser.html" +
                 "#supported-ini-file-structure", indent)
    
    

def validate_util(url, name):
    local = os.path.join(FIXEDPATHS.USERDIR, url.rsplit('/', 1)[-1])  # @UndefinedVariable
    if not os.path.exists(FIXEDPATHS.USERDIR):  # @UndefinedVariable
        logging.warn("No path found for hydrant utilities, creating %s",
                     FIXEDPATHS.USERDIR)  # @UndefinedVariable
        os.mkdir(FIXEDPATHS.USERDIR)  # @UndefinedVariable
    if not os.path.exists(local):
        logging.warn("%s not found. Downloading from %s to %s.",
                     name, url, local)
        urlretrieve(url, local)
    return local

def validate(wdl, inputs_json='tests/inputs.json'):
    config = ConfigLoader().config.All
    WDLTOOL = validate_util(config.WDLtool, "wdltool")
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

def test(wdl, inputs_json='tests/inputs.json'):
    config = ConfigLoader().config.All
    runcromw = os.path.join(FIXEDPATHS.UTILS, 'runcromw.sh')  # @UndefinedVariable
    CROMWELL = validate_util(config.Cromwell, "Command-line cromwell")
    try:
        check_call([runcromw, CROMWELL, wdl, inputs_json])
    except:
        logging.exception('Workflow test failed')
        sys.exit(1)

def config():
    pass

def main(args=None):
    
    parser = ArgumentParser(description="Hydrant: A tool for installing " +
                                        "workflows into FireCloud")
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)
    subparsers = parser.add_subparsers(dest='subcmd')
    subparsers.add_parser('init', help="Create a directory tree under the " +
                          "current one with structure and templates to " +
                          "facilitate building a FireCloud workflow or a " +
                          "docker image for use in one", add_help=False)
    dockerparser = subparsers.add_parser('docker', help='''Docker commands and
                                         convenience utilities''')
    dockercommand = dockerparser.add_subparsers(dest='dockercmd')
    dockercommand.add_parser('build', help="Build the docker image defined " +
                             "in the local Dockerfile", add_help=False)
    dockercommand.add_parser('push', help="Push the docker image to dockerhub",
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
    
    args, argv = parser.parse_known_args(args)
    
    if not os.path.isdir(FIXEDPATHS.USERDIR):  # @UndefinedVariable
        first_run()
    if not os.path.isfile(os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')):  # @UndefinedVariable
        copy_cfg()
    
    # TODO: Build a dict of hydrant arguments with values being the function to
    #       call, it will make the below a lot cleaner.
    wdl = os.path.basename(os.getcwd()) + ".wdl"
    if args.subcmd == 'init':
        init(argv)
    elif args.subcmd == 'validate':
        validate(wdl)
    elif args.subcmd == 'test':
        test(wdl)
    elif args.subcmd == 'install':
        install(argv)
    elif args.subcmd == 'docker':
        if args.dockercmd == 'build':
            build(argv)
        elif args.dockercmd == 'push':
            push(argv)
    
if __name__ == '__main__':
    main()
else:
    __version__ = get_distribution(__name__.split('.', 1)[0]).version
