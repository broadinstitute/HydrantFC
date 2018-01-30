# encoding: utf-8

'''
Classes to assist in basic WDL parsing:
    Task: Holds single WDL task and basic information about it
    WDL:  Holds workflow and an OrderedDict of Tasks
'''
from collections import OrderedDict

#TODO: enable parsing and manipulation of docker version string
class Task(object):
    '''
    Hold Single WDL task and basic information about it.
    '''

    def __init__(self, text):
        '''
        text: the text of a task section of a WDL
        '''
        self._text = text.rstrip()
        self._name = self._parse_name()
        
    def _parse_version(self):
        pass
    
    def _parse_name(self):
        return self._text.split(None, 2)[1]
    
    @property
    def name(self):
        return self._name
    
    @property
    def text(self):
        return self._text
        
        
class WDL(object):
    '''
    Hold the workflow text and an OrderedDict of Tasks.
    '''

    def __init__(self, wdl_file):
        '''
        wdl_file: the path to a wdl
        '''
        self._tasks = OrderedDict()
        self._workflow = None
        self._parse_wdl(wdl_file)
    
    def _parse_wdl(self, wdl_file):
        task = None
        with open(wdl_file, 'r') as wdl:
            for line in wdl:
                if line.startswith('task'):
                    if task is not None:
                        task = Task(task)
                        self._tasks[task.name] = task
                    task = line
                elif line.startswith('workflow'):
                    self._workflow = line
                    if task is not None:
                        task = Task(task)
                        self._tasks[task.name] = task
                elif self._workflow is None:
                    task += line
                else:
                    self._workflow += line

    @property
    def tasks(self):
        return self._tasks

    @property
    def workflow(self):
        return self._workflow

    def text(self):
        tasks = ""
        for task in self._tasks:
            tasks += task.text + "\n\n"
        return tasks + self._workflow
