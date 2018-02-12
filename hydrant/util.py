import sys
import os
import argparse

from collections import namedtuple
from pkg_resources import resource_filename
from gettext import gettext as _

FixedPaths = namedtuple('FixedPaths', 'USERDIR UTILS DEFAULTS')

FIXEDPATHS = FixedPaths(
    USERDIR          = os.path.expanduser(os.path.join("~", ".hydrant")),
    UTILS            = resource_filename(__name__, 'util'),
    DEFAULTS         = resource_filename(__name__, 'defaults')
    )

from ConfigLoader import ConfigLoader

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
