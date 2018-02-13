#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from subprocess import check_call, check_output
from pkg_resources import get_distribution
from util import ArgumentParser, initialize_user_dir

__version__ = "TESTING"

def install_commands(parsers, commands):
    import importlib
    for cmd in commands:
        prefix = "" if os.path.exists(cmd+".py") else "hydrant."
        mod = importlib.import_module(prefix+cmd)
        parser = parsers.add_parser(cmd, help=mod.Description, add_help=False)
        parser.set_defaults(func=mod.main)

def main(args=None):
 
    parser = ArgumentParser(description="Hydrant: a tool which aims to "\
        "simplify and accelerate the development and maintenance of workflows"\
        "for FireCloud (FC).")
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + __version__)

    subparsers = parser.add_subparsers(dest='subcmd')
    install_commands(subparsers, ['init', 'build','push', 'validate', 'test'])
    install_commands(subparsers, ['tutorial', 'sync', 'install', 'config'])

    args, argv = parser.parse_known_args(args)
    initialize_user_dir()
    result = args.func(argv)

if __name__ == '__main__':
    main()
else:
    __version__ = get_distribution(__name__.split('.', 1)[0]).version
