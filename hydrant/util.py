
import sys
import os
import logging
from shutil import copy2 as cp
from collections import namedtuple
from pkg_resources import resource_filename
from six.moves.urllib.request import urlretrieve

FixedPaths = namedtuple('FixedPaths', 'USERDIR BIN DEFAULTS')

FIXEDPATHS = FixedPaths(
    USERDIR          = os.path.expanduser(os.path.join("~", ".hydrant")),
    BIN              = resource_filename(__name__, 'bin'),
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

def find_tool(url, name):
    # Look for local instance of tool with given name, download if necessary
    local = os.path.join(FIXEDPATHS.USERDIR, url.rsplit('/', 1)[-1])  # @UndefinedVariable
    if not os.path.exists(FIXEDPATHS.USERDIR):  # @UndefinedVariable
        logging.info("No path found for hydrant utilities, creating %s",
                     FIXEDPATHS.USERDIR)  # @UndefinedVariable
        os.mkdir(FIXEDPATHS.USERDIR)  # @UndefinedVariable
    if not os.path.exists(local):
        logging.info("%s not found. Downloading from %s to %s.",
                     name, url, local)
        urlretrieve(url, local)
    return local

def initialize_user_dir():

    # Ensure custom Hydrant directory exists for user
    if not os.path.isdir(FIXEDPATHS.USERDIR):  # @UndefinedVariable
        logging.info("First run of hydrant, creating %s", FIXEDPATHS.USERDIR)  # @UndefinedVariable
        os.mkdir(FIXEDPATHS.USERDIR)  # @UndefinedVariable

    # Ensure that it contains a default config file
    if not os.path.isfile(os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')):  # @UndefinedVariable
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
