#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import docker
import logging
import json
from util import ArgumentParser, docker_repos, add_default_arg
from ConfigLoader import ConfigLoader, SafeConfigParser

def get_full_tag(reg, namespc, repo, tag=None):
    full_tag = namespc + '/' + repo
    if reg is not None:
        full_tag = reg + '/' + full_tag
    if tag is not None:
        full_tag += ':' + tag
    return full_tag

def extract_full_tag(full_tag):
    chunks = full_tag.split('/')
    repo, tag = chunks[-1].rsplit(':', 1)
    namespace = chunks[-2]
    reg = None
    if len(chunks) == 3:
        reg = chunks[0]
    return reg, namespace, repo, tag

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
        
    reg, namespace, _, tag = extract_full_tag(tag)
    task_cfg = SafeConfigParser(allow_no_value=True)
    task_cfg.add_section('Docker')
    if reg is not None:
        task_cfg.set('Docker', 'Registry', reg)
    task_cfg.set('Docker', 'Namespace', namespace)
    task_cfg.set('Docker', 'Tag', tag)
    
    with open(os.path.join(path, 'hydrant.cfg'), 'wb') as task_cfg_file:
        task_cfg.write(task_cfg_file)
        
    
        
def main(args=None):
    repos = {repo: version for repo, version in docker_repos()}
    docker_cfg = ConfigLoader().config.Docker
    # TODO: allow multiple registries and namespaces from the workspace folder
    #       level.
    reg_kwargs = {'help': "Host[:port] of registry if not at Docker Hub"}
    if docker_cfg.Registry is not None:
        add_default_arg(docker_cfg.Registry, reg_kwargs)
    ns_kwargs = {'help': 'Namespace under which the repository resides'}
    if docker_cfg.Namespace is not None:
        add_default_arg(docker_cfg.Namespace, ns_kwargs)
    else:
        ns_kwargs['required'] = True
    repo_kwargs = {'help': 'Repository name[:tag]'}
    # TODO: Allow arbitrary repo names and uncomment below code. For now repo
    #       names must match task folder names.
#     if len(repos) == 1 and cwd in repos:
#         repo_kwargs['help'] += ' (default: %(default)s)'
#         repo_kwargs['default'] = os.path.basename(cwd) + ':' + repos[cwd]
    if len(repos) > 0:
        repo_kwargs['choices'] = sorted(os.path.basename(repo) + ':' + version
                                        for repo, version in repos.items())
        if len(repos) > 1:
            repo_kwargs['nargs'] = '*'
        else:
            repo_kwargs['nargs'] = '?'
            repo_kwargs['metavar'] = repo_kwargs['choices'][0]
            repo_kwargs['const'] = repo_kwargs['metavar']
            repo_kwargs['default'] = repo_kwargs['metavar']
    else:
        repo_kwargs['help'] += ''', requires hydrant.cfg file if building
                               multiple images with tags other than "latest"'''
        
    parser = ArgumentParser(description="Build docker image")
    # Because parser.prog is initialized to the name of the top-level calling
    # module, it needs to be modified here to be consistent.
    # (i.e. so hydrant docker build -h returns a usage that begins with
    # hydrant docker build rather than only hydrant)
    if __name__ != '__main__':
        parser.prog += " docker " + __name__.rsplit('.', 1)[-1]
    parser.add_argument('-R', '--registry',
                        **reg_kwargs)
    parser.add_argument('-n', '--namespace', **ns_kwargs)
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
        all_repos = {os.path.basename(path): path for path in repos}
        if isinstance(args.repository, list):
            user_repos = [repo.split(':', 1)[0] for repo in args.repository]
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
            repo = args.repository.split(':', 1)[0]
            build_image(parser.prog, client, all_repos[repo], tag)
    else:
        logging.error("No repository specified.")
        sys.exit(1)

if __name__ == '__main__':
    main()
