# encoding: utf-8

from collections import defaultdict
import os
import platform
import subprocess
import sys
import time

import docker
from hydrant.ConfigLoader import ConfigLoader

# Convenient shorthands for readability
from docker.errors import APIError as apiError
from requests.exceptions import ConnectionError as connError

def get_version(path):
    return ConfigLoader(path).config.Docker.Tag or 'latest'

def docker_repos(path=None):
    if path is None:
        path = os.getcwd()
    for root, dirs, files in os.walk(path):
        # Don't descend more than 1 level
        if root.replace(path, '', 1).count(os.path.sep) == 1:
            del dirs[:]
        if 'Dockerfile' in files:
            del dirs[:] # no need to descend further
            yield (root, get_version(root))

__DaemonLaunchers = defaultdict(
    lambda: None,
    Darwin='open -a Docker',
    Windows=None,
    Linux=None
)

def __launch_daemon(client, interval=6, numtries=10):
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
        subprocess.check_call(launcher.split())
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
