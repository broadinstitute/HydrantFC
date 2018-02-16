# encoding: utf-8
import tempfile
import shutil
import os

def pytest_configure(config):
    """
    Setup empty temporary user directory for purposes of testing, and make it
    so os.path.expanduser() returns it instead of the user's home directory
    
    Copies relevant config files into the temporary directory
    """
    import os.path
    userdir = tempfile.mkdtemp()
    
    orig_userdir = os.path.expanduser('~')
    fissconfig = os.path.join(orig_userdir, '.fissconfig')
    gsutil_cfg = os.path.join(orig_userdir, '.gsutil')
    docker_cfg = os.path.join(orig_userdir, '.docker')
    
    if os.path.isfile(fissconfig):
        shutil.copy2(fissconfig, os.path.join(userdir, '.fissconfig'))
    if os.path.isdir(gsutil_cfg):
        shutil.copytree(gsutil_cfg, os.path.join(userdir, '.gsutil'))
    if os.path.isdir(docker_cfg):
        shutil.copytree(docker_cfg, os.path.join(userdir, '.docker'))
    
    def expanduser(path):
        if not path.startswith('~'):
            return path
        idx = path.find(os.path.sep, 1)
        if idx < 0:
            idx = len(path)
        return userdir + path[idx:]
    
    os.path.expanduser=expanduser
    config._userdir = userdir
    
    # hydrant cannot be imported until after expanduser has been monkeytyped
    from hydrant.util import initialize_user_dir
    initialize_user_dir()

def pytest_unconfigure(config):
    """
    Delete the temporary directory created by pytest_configure
    """
    shutil.rmtree(config._userdir)


