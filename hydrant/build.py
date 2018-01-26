#! /usr/bin/env python
# encoding: utf-8

import os
import docker
from argparse import ArgumentParser

def main(args=None):
    parser = ArgumentParser(description="Build docker image")
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    parser.add_argument('-n', '--namespace', required=True,
                        help='Namespace under which the repository resides')
    parser.add_argument('-r', '--repository',
                        default=os.path.basename(os.getcwd()),
                        help='Repository name (default: %(default)s)')
    parser.add_argument('-t', '--tag', help="Version of the image or task " + \
                        "(default: latest)")
    
    args = parser.parse_args(args)
    
    repo = args.namespace + '/' + args.repository
    if args.tag is not None:
        repo += ':' + args.tag
    
    client = docker.from_env()
    client.images.build(path='.', tag=repo, rm=True)

if __name__ == '__main__':
    main()