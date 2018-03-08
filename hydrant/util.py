# encoding: utf-8
import os
import sys
import logging
import argparse
import requests
from colorlog import ColoredFormatter
from textwrap import TextWrapper
from shutil import copy2 as cp
from io import open
from collections import namedtuple
from pkg_resources import resource_filename, get_distribution
from six import u
from six.moves import input
from six.moves.urllib.request import urlretrieve
from gettext import gettext as _

FixedPaths = namedtuple('FixedPaths', 'USERDIR BIN DEFAULTS')

FIXEDPATHS = FixedPaths(
    USERDIR          = os.path.expanduser(os.path.join("~", ".hydrant")),
    BIN              = resource_filename(__name__, 'bin'),
    DEFAULTS         = resource_filename(__name__, 'defaults')
    )

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

class ArgParser(argparse.ArgumentParser):
    def error(self, message):
        """error(message: string)

        Prints a help message incorporating the message to stderr and
        exits.
        
        If too few arguments, simply prints help and exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        prefix = '-' if '-' in self.prefix_chars else self.prefix_chars[0]
        py3_missing_args = 'the following arguments are required: '
        if 'too few arguments' in message or py3_missing_args in message \
           and sum(arg.startswith(prefix) for arg in 
                   message.rsplit(': ', 1)[-1].split(', ')) == 0:
            self.print_help()
            self.exit()
        self.exit(2, _('%s: error: %s\n\n%s\n') % (self.prog, message,
                                                   self.format_help()))

def version():
    return get_distribution(__name__.split('.', 1)[0]).version

# derived from
# https://github.com/requests/requests/issues/885#issuecomment-216838596
# The urlretrieve function that is part of urllib uses 
def urlretrieve(url, local):
    """
    The urlretrieve function that is part of urllib uses whatever version of
    OpenSSL is available locally. By using the requests library (via the
    requests[security] requirement in setup.py), we bypass that in favor of the
    latest version. This simplifies usage on OS X and Windows.
    """
    r = requests.get(url, stream=True)
    with open(local, 'wb') as f:
        for chunk in r.iter_content():
                f.write(chunk)

def add_default_arg(arg, kwargs):
    kwargs['default'] = arg
    kwargs['help'] += " (default: %(default)s)"

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
        try:
            urlretrieve(url, local)
        except IOError:
            logging.exception('Unable to download %s. If the below exception' +
                              ' includes "%s", a TLS v1.2 compatible python ' +
                              'installation is required (stock OS X does not' +
                              ' include the necessary OpenSSL version). For ' +
                              'an OS X option, see:\n' +
                              'http://docs.python-guide.org/en/latest/' +
                              'starting/install/osx', url,
                              '[SSL: TLSV1_ALERT_PROTOCOL_VERSION]')
            sys.exit(74) # sysexits.h IOERR exit status
        except:
            logging.exception('Unable to download %s.', url)
            sys.exit(1)
            
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
    old_version = None
    cur_version = version()
    version_file = os.path.join(FIXEDPATHS.USERDIR, 'VERSION')
    version_conflict_action = None
    
    # Ensure custom Hydrant directory exists for user
    if not os.path.isdir(FIXEDPATHS.USERDIR):
        logging.info("First run of hydrant, creating %s", FIXEDPATHS.USERDIR)
        os.mkdir(FIXEDPATHS.USERDIR)
        with open(version_file, 'w') as version_fp:
            version_fp.write(u(cur_version + "\n"))

    # Check that version of .hydrant matches hydrant version
    if os.path.isfile(version_file):
        with open(version_file, 'r') as version_fp:
            old_version = version_fp.read().strip()
    
    if cur_version != old_version:
        logging.info("User template and config files are from an older " +
                     "version, and may need to be updated to ensure proper " +
                     "functionality.")
        while version_conflict_action is None:
            version_conflict_action = \
                input("(R)eplace, (B)ackup, (S)kip: ").strip()
            if version_conflict_action.lower() in ('r', 'replace'):
                version_conflict_action = 'replace'
                logging.info("Replacing existing template and config files " +
                             "with the latest versions.")
            elif version_conflict_action.lower() in ('b', 'backup'):
                version_conflict_action = 'backup'
                logging.info("Creating backups of existing template and " +
                             "config files, and adding latest versions.")
            elif version_conflict_action.lower() in ('s', 'skip'):
                version_conflict_action = 'skip'
                logging.warn("Skipping updating existing template and " +
                             "config files. Please note that this may cause " +
                             "unexpected failures. To bring this dialog " +
                             "back, delete the VERSION file in %s before " +
                             "running hydrant again.", FIXEDPATHS.USERDIR)
            else:
                logging.warn("Unknown argument: %s", version_conflict_action)
                version_conflict_action = None

    # Ensure that it contains a default config file
    if not os.path.isfile(os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')):
        _initialize_user_cfg()
    elif version_conflict_action is not None \
         and version_conflict_action != 'skip':
        _initialize_user_cfg(version_conflict_action == 'backup')
    
    # Ensure that it contains a wdl template file
    if not os.path.isfile(os.path.join(FIXEDPATHS.USERDIR, 'templates.py')):
        _initialize_templates()
    elif version_conflict_action is not None \
         and version_conflict_action != 'skip':
        _initialize_templates(version_conflict_action == 'backup')
        
    # Update VERSION if necessary
    if version_conflict_action is not None:
        with open(version_file, 'w') as version_fp:
            version_fp.write(u(cur_version + "\n"))

def _initialize_user_cfg(backup=False):
    user_cfg = os.path.join(FIXEDPATHS.DEFAULTS, 'user.cfg')
    hydrant_cfg = os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')
    if backup and os.path.isfile(hydrant_cfg):
        hydrant_bak = hydrant_cfg + '.bak'
        logging.info("Backing up %s to %s", hydrant_cfg, hydrant_bak)
        cp(hydrant_cfg, hydrant_bak)
    logging.info('Generating initial hydrant.cfg')
    cp(user_cfg, hydrant_cfg)
    logging.info("%s added. You may edit using INI file structure and basic " +
                 "interpolation as defined here:\n" +
                 "\thttps://docs.python.org/3/library/configparser.html" +
                 "#supported-ini-file-structure\nWorkspaces list may be " +
                 "defined with commas (Workspaces=ws1,ws2,ws3).", hydrant_cfg)

def _initialize_templates(backup=False):
    default_templates = os.path.join(FIXEDPATHS.DEFAULTS, 'templates.py')
    user_templates = os.path.join(FIXEDPATHS.USERDIR, 'templates.py')
    if backup and os.path.isfile(user_templates):
        templates_bak = user_templates + '.bak'
        logging.info("Backing up %s to %s", user_templates, templates_bak)
        cp(user_templates, templates_bak)
    logging.info('Generating initial templates.py')
    cp(default_templates, user_templates)
    logging.info("%s added. You may edit using python string.Template " +
                 "notation:\n\thttps://docs.python.org/3/tutorial/" +
                 "stdlib2.html#templating\n" +
                 "See doc and comments in the file for details.",
                 user_templates)
