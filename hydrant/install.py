#! /usr/bin/env python
# encoding: utf-8

import os
from argparse import ArgumentDefaultsHelpFormatter, ArgumentTypeError
from firecloud.fiss import meth_new, meth_set_acl
from firecloud.fccore import __fcconfig as fcconfig
from hydrant.util import ArgParser, initialize_logging
from hydrant.ConfigLoader import ConfigLoader
from six import string_types

Description = 'Installs workflow(s) into the FC method repository'

def ValidFile(filename):
    if not os.path.isfile(filename):
        raise ArgumentTypeError(filename + " was not found on the filesystem")
    return filename

def acl_kwargs(acl, cfg):
    kwargs = {'metavar': 'user', 'nargs': '*',
              'help': 'User(s) to be given ' + acl.title() + \
                      ' access to method'}
    if cfg is not None:
        if isinstance(cfg, string_types):
            kwargs['default'] = [cfg]
        else:
            kwargs['default'] = cfg
    return kwargs

def set_acl(role, args):
    attr = getattr(args, role.lower() + 's')
    if attr:
        args.users = attr
        args.role = role.upper()
        meth_set_acl(args)

def main(args=None):
    method_name = os.path.basename(os.getcwd())
    wdl = method_name + '.wdl'
    firecloud_cfg = ConfigLoader().config.FireCloud  # @UndefinedVariable
    
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
    parser.add_argument('-o', '--owners',
                        **acl_kwargs('owner', firecloud_cfg.Owners))
    parser.add_argument('-r', '--readers',
                        **acl_kwargs('reader', firecloud_cfg.Readers))
    parser.add_argument('-w', '--writers',
                        **acl_kwargs('writer', firecloud_cfg.Writers))
    
    args = parser.parse_args(args)
    
    meth_new(args)
    args.snapshot_id = None
    set_acl('owner', args)
    set_acl('reader', args)
    set_acl('writer', args)

if __name__ == '__main__':
    initialize_logging()
    main()
