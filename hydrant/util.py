import sys
import os

from collections import namedtuple
from pkg_resources import resource_filename

FixedPaths = namedtuple('FixedPaths', 'USERDIR UTILS DEFAULTS')

FIXEDPATHS = FixedPaths(
    USERDIR          = os.path.expanduser(os.path.join("~", ".hydrant")),
    UTILS            = resource_filename(__name__, 'util'),
    DEFAULTS         = resource_filename(__name__, 'defaults')
    )

from ConfigLoader import ConfigLoader

def help_if_no_args(parser, args):
    prefix = '-' if '-' in parser.prefix_chars else parser.prefix_chars[0]
    if args is not None and len(args) == 0:
        return [prefix + 'h']
    if args is None and len(sys.argv) == len(parser.prog.split()):
        return [prefix + 'h']
    return args

def add_default_arg(arg, kwargs):
    kwargs['default'] = arg
    kwargs['help'] += " (default: %(default)s)"

def get_version(path):
    return ConfigLoader(path).config.Docker.Tag or 'latest'

def docker_repos(path=os.getcwd()):
    for root, dirs, files in os.walk(path):
        # Don't descend more than 1 level
        if root.replace(path, '', 1).count(os.path.sep) == 1:
            del dirs[:]
        if 'Dockerfile' in files:
            del dirs[:] # no need to descend further
            yield (root, get_version(root))
