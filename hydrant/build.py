#! /usr/bin/env python
# encoding: utf-8

import os
import docker
from argparse import ArgumentParser

def main(args=None):
    tag=None
    if os.path.isfile('VERSION'):
        with open('VERSION') as version:
            for count, line in enumerate(version):
                tag = line.strip()
            if count > 0:
                raise ValueError('VERSION file should only contain 1 line')
    parser = ArgumentParser(description="Build docker image")
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    parser.add_argument('-R', '--registry',
                        help="Host[:port] of registry if not at Docker Hub")
    parser.add_argument('-n', '--namespace', required=True,
                        help='Namespace under which the repository resides')
    parser.add_argument('-r', '--repository',
                        default=os.path.basename(os.getcwd()),
                        help='Repository name (default: %(default)s)')
    parser.add_argument('-t', '--tag', help="Version of the image or task " + \
                        "(default: {})".format(tag or "latest"), default=tag)
    
    args = parser.parse_args(args)
    
    repo = args.namespace + '/' + args.repository
    if args.tag is not None:
        repo += ':' + args.tag
    if args.registry is not None:
        repo = args.registry + '/' + repo
    
    client = docker.from_env()
    client.images.build(path='.', tag=repo, rm=True)

if __name__ == '__main__':
    main()