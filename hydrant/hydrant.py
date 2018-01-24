#! /usr/bin/env python
# encoding: utf-8

import os
import logging
import subprocess
from argparse import ArgumentParser

from collections import namedtuple
from six.moves.urllib.request import urlretrieve

from init import main as init

Defaults = namedtuple('Defaults',
                      'HYDRANTBIN CROMWELL_RELEASE WDLTOOL_RELEASE')

def validate_util(hydrantbin, url, name):
    local = os.path.join(hydrantbin, url.rsplit('/', 1)[-1])
    if not os.path.exists(hydrantbin):
        logging.warn("No path found for hydrant utilities, creating %s",
                     hydrantbin)
        os.mkdir(hydrantbin)
    if not os.path.exists(local):
        logging.warn("%s not found. Downloading from %s to %s.",
                     name, url, local)
        urlretrieve(url, local)
    return local

def main():
    defaults = Defaults(
        HYDRANTBIN = os.path.expanduser(os.path.join(os.environ("~"),
                                                     ".hydrantutil")),
        CROMWELL_RELEASE = "https://github.com/broadinstitute/cromwell/" +
                           "releases/download/29/cromwell-29.jar",
        WDLTOOL_RELEASE = "https://github.com/broadinstitute/wdltool/" +
                          "releases/download/0.14/wdltool-0.14.jar"
        )
    
    parser = ArgumentParser(description="Hydrant: A tool for installing " +
                                        "workflows into FireCloud")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('init', action='store_true',
                       help="Create a directory tree under the current one " +
                       "with structure and templates to facilitate building " +
                       "a FireCloud workflow or a docker image for use in one")
    group.add_argument('build', action='store_true', help="Build the docker " +
                       "image defined in the local Dockerfile")
    group.add_argument('publish', action='store_true',
                       help="Push the docker image to dockerhub")
    group.add_argument('sync', action='store_true',
                       help="Update the WDLs of all local workflows using " +
                       "this docker image to the latest version")
    group.add_argument('validate', action='store_true', help="Run wdltool to" +
                       " validate the WDL and generate initial inputs.json")
    group.add_argument('test', action='store_true', help="Run command-line " +
                       "cromwell to test the workflow defined in the WDL " +
                       "with test data specified in inputs.json")
    group.add_argument('install', action='store_true',
                       help="Push WDL to your FireCloud method repository")
    group.add_argument('config', action='store_true',
                       help="Update workspace task configs with the latest " +
                       "snapshot you have committed")
    
    args, opts = parser.parse_known_args()
    
    # TODO: Build a dict of hydrant arguments with values being the function to
    #       call, it will make the below a lot cleaner.
    if args.init:
        init(opts)
    elif args.validate:
        WDLTOOL = validate_util(defaults.HYDRANTBIN, defaults.WDLTOOL_RELEASE, "wdltool")
        subprocess.check_call()
    elif args.test:
        CROMWELL = validate_util(defaults.HYDRANTBIN, defaults.CROMWELL_RELEASE, "Command-line cromwell")
    
if __name__ == '__main__':
    main()
