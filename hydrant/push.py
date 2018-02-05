#! /usr/bin/env python
# encoding: utf-8

import os
import docker
import logging
from argparse import ArgumentParser

def find_registry_namespace(client, repo, error_on_fail=False):
    repo_images = [str(image).split()[-1].strip("'>") \
                   for image in client.images.list() \
                   if '/' + repo + ':' in str(image)]
    namespaces = set(image.split('/')[-2] for image in repo_images)
    registries = set(image.split('/')[0] for image in repo_images
                     if image.count('/') == 2)
    registry = None
    if len(registries) == 1:
        registry = registries.pop()
    if len(namespaces) == 1:
        return registry, namespaces.pop()
    if error_on_fail:
        raise ValueError("Found %d namespaces for %s, was expecting 1." %
                         (len(namespaces), repo))
    return None, None

def add_default_arg(arg, kwargs):
    kwargs['default'] = arg
    kwargs['help'] += " (default: %(default)s)"

def main(args=None):
    parser = ArgumentParser(description="Publish docker image")
    if __name__ != '__main__':
        parser.prog += " " + __name__.rsplit('.', 1)[-1]
    try:
        client = docker.from_env()
    except:
        logging.exception("%s requires a running docker daemon. " +
                          "Please install one from %s before trying again.",
                          parser.prog,
                          "https://www.docker.com/community-edition#/download")
        
    repo = os.path.basename(os.getcwd())
    registry, namespace = find_registry_namespace(client, repo)
    
    reg_kwargs = {'help': "Host[:port] of registry if not at Docker Hub"}
    if registry is not None:
        add_default_arg(registry, reg_kwargs)
    parser.add_argument('-R', '--registry', **reg_kwargs)
    
    ns_kwargs = {'help': 'Namespace under which the repository resides'}
    if namespace is None:
        ns_kwargs['required'] = True
    else:
        add_default_arg(namespace, ns_kwargs)
    parser.add_argument('-n', '--namespace', **ns_kwargs)
    parser.add_argument('-r', '--repository', default=repo,
                        help='Repository name (default: %(default)s)')
    parser.add_argument('-t', '--tag', help="Version of the image or task " + \
                        "(default: latest)")
    
    args = parser.parse_args(args)
    
    repo = args.namespace + '/' + args.repository
    if args.registry is not None:
        repo = args.registry + '/' + repo
    
    push_kwargs = {'stream': True}
    if args.tag is not None:
        push_kwargs['tag'] = args.tag
    
    for line in client.images.push(repo, **push_kwargs):
        logging.info(line)

if __name__ == '__main__':
    main()
