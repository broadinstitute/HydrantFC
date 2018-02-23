# encoding: utf-8

import pytest
import subprocess
from platform import system
from hydrant.util import connect_to_daemon
from time import sleep
 
# For now, launching the docker daemon only works on Mac OSX (Darwin). As more
# systems are added, the below list can be expanded
@pytest.mark.skipif(system() not in ['Darwin'], reason="Unsupported OS")
def test_relaunch_docker_daemon():
    user_running_daemon = True
    # check for presence of running Docker daemon, and kill it if necessary
    try:
        pid = subprocess.check_output("ps -xc | grep 'Docker$'",
                                      shell=True,
                                      stderr=subprocess.STDOUT
                                      ).strip().split()[0]
    except subprocess.CalledProcessError:
        # Daemon not currently running
        user_running_daemon = False
    else:
        # Daemon is running, so kill it
        subprocess.check_call(['kill', pid])
        sleep(10) # give time to finish exiting
    connect_to_daemon()
     
    # Return system to its starting state
    if not user_running_daemon:
        pid = subprocess.check_output("ps -xc | grep 'Docker$'",
                                      shell=True,
                                      stderr=subprocess.STDOUT
                                      ).strip().split()[0]
        subprocess.check_call(['kill', pid])
