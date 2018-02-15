import os
from colorlog import ColoredFormatter
import logging
from textwrap import TextWrapper
import argparse
from shutil import copy2 as cp
from collections import namedtuple
from pkg_resources import resource_filename
from six.moves.urllib.request import urlretrieve
from gettext import gettext as _
import docker
import time
import subprocess
import sys

# Convenient shorthands for readability
from requests.exceptions import ConnectionError as connError
from docker.errors import APIError as apiError

import platform
from collections import defaultdict

FixedPaths = namedtuple('FixedPaths', 'USERDIR BIN DEFAULTS')

FIXEDPATHS = FixedPaths(
    USERDIR          = os.path.expanduser(os.path.join("~", ".hydrant")),
    BIN              = resource_filename(__name__, 'bin'),
    DEFAULTS         = resource_filename(__name__, 'defaults')
    )

from ConfigLoader import ConfigLoader

# based on https://stackoverflow.com/a/25335783
class WrappedColoredFormatter(ColoredFormatter):
    def __init__(self, fmt=None, datefmt=None, style='%', log_colors=None,
                 reset=True, secondary_log_colors=None, width=80, indent=9,
                 break_long_words=False, break_on_hyphens=True):
        if log_colors is None:
            log_colors = {
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            }
        super(WrappedColoredFormatter, self).__init__(fmt, datefmt, style,
                                                      log_colors, reset,
                                                      secondary_log_colors)
        self.wrapper = TextWrapper(width=width, subsequent_indent=' '*indent,
                                   break_long_words=break_long_words,
                                   break_on_hyphens=break_on_hyphens)
        
    def format(self, record):
        lines = super(WrappedColoredFormatter, self).format(record).splitlines()
        wrapped_lines = []
        initial_indent = self.wrapper.initial_indent
        for idx, line in enumerate(lines):
            wrapped_lines.extend(self.wrapper.wrap(line))
            if idx == 0:
                self.wrapper.initial_indent = self.wrapper.subsequent_indent
        
        self.wrapper.initial_indent = initial_indent
            
        return "\n".join(wrapped_lines)

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        """error(message: string)

        Prints a help message incorporating the message to stderr and
        exits.
        
        If too few arguments, simply prints help and exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        if 'too few arguments' in message:
            self.print_help()
            self.exit()
        self.exit(2, _('%s: error: %s\n\n%s\n') % (self.prog, message,
                                                   self.format_help()))

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
    local = os.path.join(FIXEDPATHS.USERDIR, url.rsplit('/', 1)[-1])
    if not os.path.exists(FIXEDPATHS.USERDIR):
        logging.info("No path found for hydrant utilities, creating %s",
                     FIXEDPATHS.USERDIR)
        os.mkdir(FIXEDPATHS.USERDIR)
    if not os.path.exists(local):
        logging.info("%s not found. Downloading from %s to %s.",
                     name, url, local)
        urlretrieve(url, local)
    return local

def initialize_logging():
    # Set root logger
    
    stream_formatter = WrappedColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s%(white)s %(message)s"
    )
    logger = logging.getLogger()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    
def log_to_logfile(logfile):
    logger = logging.getLogger()
    file_formatter = WrappedColoredFormatter(
        "%(asctime)s::%(log_color)s%(levelname)-8s%(reset)s%(white)s %(message)s",
        datefmt='%Y-%m-%d %I:%M:%S',
        indent = 30
    )
    file_handler = logging.FileHandler(logfile, delay=True)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

def initialize_user_dir():

    # Ensure custom Hydrant directory exists for user
    if not os.path.isdir(FIXEDPATHS.USERDIR):
        logging.info("First run of hydrant, creating %s", FIXEDPATHS.USERDIR)
        os.mkdir(FIXEDPATHS.USERDIR)

    # Ensure that it contains a default config file
    if not os.path.isfile(os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')):
        user_cfg = os.path.join(FIXEDPATHS.DEFAULTS, 'user.cfg')
        hydrant_cfg = os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')
        logging.info('Generating initial hydrant.cfg')
        cp(user_cfg, hydrant_cfg)
        logging.info("%s added. You may edit using INI file structure and " +
                     "basic interpolation as defined here:\n" +
                     "\thttps://docs.python.org/3/library/configparser.html" +
                     "#supported-ini-file-structure\nWorkspaces list may be " +
                     "defined with commas (Workspaces=ws1,ws2,ws3).",
                     hydrant_cfg)
    
    # Ensure that it contains a wdl template file
    if not os.path.isfile(os.path.join(FIXEDPATHS.USERDIR, 'templates.py')):
        default_templates = os.path.join(FIXEDPATHS.DEFAULTS, 'templates.py')
        user_templates = os.path.join(FIXEDPATHS.USERDIR, 'templates.py')
        logging.info('Generating initial templates.py')
        cp(default_templates, user_templates)
        logging.info("%s added. You may edit using python string.Template " +
                     "notation:\n\thttps://docs.python.org/3/tutorial/" +
                     "stdlib2.html#templating\n" +
                     "See doc and comments in the file for details.",
                     user_templates)

__DaemonLaunchers = defaultdict(
    lambda: None,
    Darwin='open -a Docker',
    Windows=None,
    Linux=None
)

def __launch_daemon(client, interval=3, numtries=10):
    # TODO: change from sys.stderr.write to logging.error/logging.exception, as
    # sys.stderr.write is bufferred
    stderr = sys.stderr.write
    which = platform.system()
    launcher = __DaemonLaunchers.get(which, None)
    if not launcher:
        stderr("Docker daemon is not running, and this tool does not yet ")
        stderr("provide\nauto start for %s; please start manually.\n" % which)
        sys.exit(1)

    # Launch daemon ...
    stderr("Docker daemon not running, launching now ")
    try:
        subprocess.check_output(launcher.split(), stderr=subprocess.STDOUT)
    except Exception as error:
        stderr("\nCould not find/launch daemon: %s\n\t%s\n" % (launcher, error))
        stderr("Docker can be downloaded from\n"+\
                "\thttps://www.docker.com/community-edition#/download\n")
        sys.exit(2) # Posix errno 2: no such file or directory

    # Then try to connect ...
    while True and numtries > 0:
        try:
            result = client.ping()
            stderr("connected!\n")
            return
        except (connError, apiError):
            stderr('.')
            time.sleep(interval)
        numtries -= 1
    stderr("Failed to launch or connect to container daemon")
    sys.exit(3) # Posix errno 3: no such process

def connect_to_daemon():

    client = docker.from_env()
    try:
        result = client.ping()
    except connError:
        __launch_daemon(client)
    return client
