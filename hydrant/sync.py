#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from util import ArgumentParser
from argparse import ArgumentTypeError

Description = 'Update WDLs of local workflows which use this Docker'

def sync():
    logging.info("The sync command is not implemented yet")

def main(args=None):
    parser = ArgumentParser(description=Description + \
                    ', to the latest version of its image')
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]

    args = parser.parse_args(args)
    sync()

if __name__ == '__main__':
    main()
