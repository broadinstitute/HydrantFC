#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
from hydrant.util import ArgParser

Description = "Update FC method configurations for this workflow"

def config():
    logging.info("The config command is not implemented yet")

def main(args=None):
    parser = ArgParser(description=Description+\
		" to reflect the latest method snapshot")
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    
    args = parser.parse_args(args)
    config()

if __name__ == '__main__':
    main()
