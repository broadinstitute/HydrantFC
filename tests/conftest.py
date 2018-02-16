# encoding: utf-8
import pytest
import tempfile
import shutil

def pytest_configure(config):
    """
    Setup empty temporary user directory for purposes of testing, and make it
    so os.path.expanduser() returns it instead of the user's home directory
    """
    import os.path
    userdir = tempfile.mkdtemp()
    def expanduser(path):
        if not path.startswith('~'):
            return path
        idx = path.find(os.path.sep, 1)
        if idx < 0:
            idx = len(path)
        return userdir + path[idx:]
    os.path.expanduser=expanduser
    config._userdir = userdir

def pytest_unconfigure(config):
    """
    Delete the temporary directory created by pytest_configure
    """
    shutil.rmtree(config._userdir)


