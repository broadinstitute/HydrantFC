#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import docker
import logging
import json
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

def build_image(name, client, path, tag):
    try:
        for result in client.images.build(path=path, tag=tag, rm=True)[1]:
            logging.info(json.dumps(result).rstrip().replace(r'\n', ''))
    except:
        logging.exception("%s requires a running docker daemon. Please " +
                          "start or install one from %s before trying again.",
                          name,
                          "https://www.docker.com/community-edition#/download")
        sys.exit(1)
        
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
    
    client = docker.from_env()
    
    if args.all:
        for repo, version in repos.items():
            tag = get_full_tag(args.registry, args.namespace,
                               os.path.basename(repo), version)
            build_image(parser.prog, client, repo, tag)
    elif args.repository:
        if isinstance(args.repository, list):
            user_repos = [repo.split(':', 1)[0] for repo in args.repository]
            all_repos = {os.path.basename(path): path for path in repos}
            # Only build images if all user-specified ones are available
            build_images = set(user_repos).issubset(set(all_repos.keys()))
            for idx, repo in enumerate(args.repository):
                tag = get_full_tag(args.registry, args.namespace, repo)
                user_repo = user_repos[idx]
                if user_repo in all_repos:
                    if build_images:
                        build_image(parser.prog, client, all_repos[user_repo],
                                    tag)
                else:
                    logging.error("Could not find a path for %s. Please ensure" + \
                                  " the directory containing the Dockerfile " + \
                                  "matches the name of the repository.", tag)
            if not build_images:
                sys.exit(1)
        else:
            tag = get_full_tag(args.registry, args.namespace, args.repository)
            build_image(parser.prog, client, '.', tag)
    else:
        logging.error("No repository specified.")
        sys.exit(1)

if __name__ == '__main__':
    main()
