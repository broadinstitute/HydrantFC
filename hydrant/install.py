#! /usr/bin/env python
# encoding: utf-8

import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentTypeError
from firecloud.fiss import meth_new
from firecloud.fccore import __fcconfig as fcconfig
from util import help_if_no_args

Description = 'Installs workflow(s) into the FC method repository'

def ValidFile(filename):
    if not os.path.isfile(filename):
        raise ArgumentTypeError("{} was not found on the filesystem".format(filename))
    return filename

def main(args=None):
    method_name = os.path.basename(os.getcwd())
    wdl = method_name + '.wdl'
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description=Description)
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    
    parser.add_argument('-m', '--method', help='Method name',
                        default=method_name)
    method_ns_kwargs = {}
    if fcconfig.method_ns:
        method_ns_kwargs['default'] = fcconfig.method_ns
    else:
        method_ns_kwargs['required'] = True
    parser.add_argument('-n', '--namespace', help="Method Repo namespace.",
                        **method_ns_kwargs)
    parser.add_argument('-d','--wdl', default=wdl, help="Method definiton, " + \
                        "as a file of WDL (Workflow Description Language)",
                        type=ValidFile)
    parser.add_argument('-s', '--synopsis', help="Short (<80 chars) " + \
                        "description of method")
    parser.add_argument('--doc', help='Optional documentation file <10Kb',
                        type=ValidFile)
    parser.add_argument('-c', '--comment', metavar='SNAPSHOT_COMMENT',
                        help='Optional comment specific to this snapshot',
                        default='')
    
    args = help_if_no_args(parser, args)
    args = parser.parse_args(args)
    
    meth_new(args)

if __name__ == '__main__':
    main()
