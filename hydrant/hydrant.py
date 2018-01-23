#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging

from six.moves.urllib.request import urlretrieve

def check_util(local, remote, name):
    if not os.path.exists(local):
        logging.warn("%s not found. Downloading from %s to %s.",
                     name, remote, local)
        urlretrieve(remote, local)

def main():
    HYDRANTBIN = os.path.expanduser(os.path.join(os.environ("~"), ".hydrantutil"))
    if not os.path.exists(HYDRANTBIN):
        logging.warn("No path found for hydrant utilities, creating %s",
                     HYDRANTBIN)
        os.mkdir(HYDRANTBIN)
    
    CROMWELL_RELEASE = "https://github.com/broadinstitute/cromwell/releases/download/29/cromwell-29.jar"
    CROMWELL = os.path.join(HYDRANTBIN, CROMWELL_RELEASE.rsplit('/', 1)[-1])
    check_util(CROMWELL, CROMWELL_RELEASE, "Command-line cromwell")
    
    WDLTOOL_RELEASE = "https://github.com/broadinstitute/wdltool/releases/download/0.14/wdltool-0.14.jar"
    WDLTOOL = os.path.join(HYDRANTBIN, WDLTOOL_RELEASE.rsplit('/', 1)[-1])
    check_util(WDLTOOL, WDLTOOL_RELEASE, "wdltool")
