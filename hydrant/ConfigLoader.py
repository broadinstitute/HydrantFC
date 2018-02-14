# encoding: utf-8

import sys
import os

from util import FIXEDPATHS
from collections import namedtuple

# SafeConfigParser was renamed to ConfigParser in Python 3.2, and the use of
# its alias deprecated. Unfortunately six does not accommodate this change.

PY32 = sys.version_info[0:2] >= (3, 2)
if PY32:
    from six.moves.configparser import ConfigParser as SafeConfigParser
else:
    from six.moves.configparser import SafeConfigParser

Config = namedtuple('Config', 'All FireCloud Docker Tasks')
AllSection = namedtuple('AllSection', 'Logfile Cromwell WDLtool')
FireCloudSection = namedtuple('FireCloudSection',
                              ['MethodNamespace', 'Workspaces', 'Synopsis',
                               'Documentation', 'SnapshotComment'])
DockerSection = namedtuple('DockerSection', 'Registry Namespace Tag')
TaskSubsection = namedtuple('TaskSubSection', ('Src',) + DockerSection._fields)

class ConfigLoader(object):
    '''
    Takes a directory and loads config files
    '''

    def __init__(self, path=os.getcwd(), cli_cfg=''):
        '''
        Constructor
        '''
        self._config = SafeConfigParser(allow_no_value=True)
        self._config.optionxform = str
        user_cfg = os.path.join(FIXEDPATHS.USERDIR, 'hydrant.cfg')  # @UndefinedVariable
        with open(user_cfg) as default_cfg:
            if PY32:
                self._config.read_file(self.readline_generator(default_cfg))
            else:
                self._config.readfp(default_cfg)
                
        workflow_cfg = ''
        task_cfg = ''
        if os.path.exists(os.path.join(path, 'Dockerfile')):
            task_cfg = os.path.join(path, 'hydrant.cfg')
            workflow_cfg = os.path.join(os.path.dirname(os.path.abspath(path)),
                                        'hydrant.cfg')
        else:
            workflow_cfg = os.path.join(path, 'hydrant.cfg')
        
        self._config.read([workflow_cfg, task_cfg, cli_cfg])
    
    # from https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.readfp
    @staticmethod
    def readline_generator(fp):
        line = fp.readline()
        while line:
            yield line
            line = fp.readline()
    
    @property
    def config(self):
        '''Build namedtuple version of config'''
        all_section  = self._get_section(AllSection, 'All')
        firecloud_section = self._get_section(FireCloudSection, 'FireCloud')
        docker_section = self._get_section(DockerSection, 'Docker')
        tasks_section = self._get_subsections(TaskSubsection, 'Task')
        return Config(all_section, firecloud_section, docker_section,
                      tasks_section)
    
    def _get_items(self, section):
        for key, value in self._config.items(section):
            if value.strip() == '': # Convert empty values to None
                value = None
            elif ',' in value: # Convert comma-separated fields to tuples
                value = tuple(field.strip() for field in value.split(','))
            yield key, value
    
    def _get_section(self, named_tuple_class, section):
        items = dict(self._get_items(section))
        return named_tuple_class._make(items.get(key) for key in named_tuple_class._fields)
    
    def _get_subsections(self, named_tuple_class, section_prefix):
        subsections = [subsection for subsection in self._config.sections() \
                       if subsection.startswith(section_prefix)]
        if len(subsections) == 0:
            return None
        Section = namedtuple(section_prefix + 's',
                             [subsection.replace(section_prefix, '').strip() \
                              for subsection in subsections])
        return Section._make(self._get_section(named_tuple_class, subsection)
                             for subsection in subsections)
        
    @staticmethod
    def array_to_cfg_str(ary):
        return ','.join(ary)
