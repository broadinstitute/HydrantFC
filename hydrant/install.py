#! /usr/bin/env python
# encoding: utf-8

import os
from argparse import ArgumentDefaultsHelpFormatter, ArgumentTypeError
from firecloud.fiss import meth_new
from firecloud.fccore import __fcconfig as fcconfig
from hydrant.util import ArgParser, initialize_logging

Description = 'Installs workflow(s) into the FC method repository'

def ValidFile(filename):
    if not os.path.isfile(filename):
        raise ArgumentTypeError("{} was not found on the filesystem".format(filename))
    return filename

def main(args=None):
    method_name = os.path.basename(os.getcwd())
    wdl = method_name + '.wdl'
    parser = ArgParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            description=Description)
    # Because parser.prog is initialized to the name of the top-level calling
    # module, it needs to be modified here to be consistent.
    # (i.e. so hydrant install -h returns a usage that begins with
    # hydrant install rather than only hydrant)
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
    
    args = parser.parse_args(args)
    
    meth_new(args)

if __name__ == '__main__':
    initialize_logging()
    main()
