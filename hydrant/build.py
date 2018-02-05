#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import docker
import logging
from argparse import ArgumentParser

def get_version(path):
    tag='latest'
    version_file = os.path.join(path, 'VERSION')
    if os.path.isfile(version_file):
        with open(version_file) as version:
            for count, line in enumerate(version):
                tag = line.strip()
            if count > 0:
                raise ValueError('VERSION file should only contain 1 line')
    return tag

def get_full_tag(reg, namespc, repo, tag=None):
    full_tag = namespc + '/' + repo
    if reg is not None:
        full_tag = reg + '/' + full_tag
    if tag is not None:
        full_tag += ':' + tag
    return full_tag
        
def main(args=None):
    repos = {}
    cwd = os.getcwd()
    for root, dirs, files in os.walk(cwd):
        # Don't descend more than 1 level
        if root.replace(cwd, '', 1).count(os.path.sep) == 1:
            del dirs[:]
        if 'Dockerfile' in files:
            repos[root] = get_version(root)
            del dirs[:] # no need to descend further
    repo_kwargs = {'help': 'Repository name[:tag]'}
    if len(repos) == 1 and cwd in repos:
        repo_kwargs['help'] += ' (default: %(default)s)'
        repo_kwargs['default'] = os.path.basename(cwd) + ':' + repos[cwd]
    elif len(repos) > 0:
        repo_kwargs['choices'] = sorted(os.path.basename(repo) + ':' + version
                                        for repo, version in repos.items())
        repo_kwargs['nargs'] = '*'
    else:
        repo_kwargs['help'] += ''', requires VERSION file if building multiple
                                  images with tags other than "latest"'''
        
    parser = ArgumentParser(description="Build docker image")
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    parser.add_argument('-R', '--registry',
                        help="Host[:port] of registry if not at Docker Hub")
    parser.add_argument('-n', '--namespace', required=True,
                        help='Namespace under which the repository resides')
    parser.add_argument('-r', '--repository', **repo_kwargs)
    parser.add_argument('-a', '--all', action='store_true',
                        help="Build all docker images.")
    
    args = parser.parse_args(args)
    
    repo = args.namespace + '/' + args.repository
    if args.registry is not None:
        repo = args.registry + '/' + repo
    
    client = docker.from_env()
    if args.all:
        for repo, version in repos.items():
            tag = get_full_tag(args.registry, args.namespace,
                               os.path.basename(repo), version)
            client.images.build(path=repo, tag=tag, rm=True)
    elif args.repository:
        user_repos = [repo.split(':', 1)[0] for repo in args.repository]
        all_repos = {os.path.basename(path): path for path in repos}
        # Only build images if all user-specified ones are available
        build_images = set(user_repos).issubset(set(all_repos.keys()))
        for idx, repo in enumerate(args.repository):
            tag = get_full_tag(args.registry, args.namespace, repo)
            user_repo = user_repos[idx]
            if user_repo in all_repos:
                if build_images:
                    client.images.build(path=all_repos[user_repo], tag=tag,
                                        rm=True)
            else:
                logging.error("Could not find a path for %s. Please ensure" + \
                              " the directory containing the Dockerfile " + \
                              "matches the name of the repository.", tag)
        if not build_images:
            sys.exit(1)
    else:
        logging.error("No repository specified.")
        sys.exit(1)
    

if __name__ == '__main__':
    main()