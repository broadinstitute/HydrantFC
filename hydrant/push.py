#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import docker
import logging
import json
from six.moves import input
from getpass import getpass
from argparse import ArgumentParser

def find_registry_namespace(client, repo, error_on_fail=False):
    repo_images = [tag for image in client.images.list() \
                   for tag in image.tags if '/' + repo + ':' in tag]
    namespaces = set(image.split('/')[-2] for image in repo_images)
    registries = set(image.split('/')[0] for image in repo_images
                     if image.count('/') == 2)
    registry = None
    if len(registries) == 1:
        registry = registries.pop()
    if len(namespaces) == 1:
        return registry, namespaces.pop()
    if error_on_fail:
        raise ValueError("Found {} namespaces for {}, was expecting 1.".format(
                         len(namespaces), repo))
    return registry, None

def get_version(path):
    tag=None
    version_file = os.path.join(path, 'VERSION')
    if os.path.isfile(version_file):
        with open(version_file) as version:
            for count, line in enumerate(version):
                tag = line.strip()
            if count > 0:
                raise ValueError('VERSION file should only contain 1 line')
    return tag

def add_default_arg(arg, kwargs):
    kwargs['default'] = arg
    kwargs['help'] += " (default: %(default)s)"

def push_image(client, repo, kwargs):
    for line in client.images.push(repo, **kwargs):
        for result in line.splitlines():
            if 'errorDetail' in result:
                result = json.dumps(json.loads(result), indent=2)
                error = ''
                for err_line in result.splitlines(True):
                    linebrk = err_line.find(r'errors:\n')
                    if linebrk >= 0:
                        brkcnt = err_line.count(r'\n')
                        err_line = err_line.replace(r'\n', ' ', 1)
                        err_line = err_line.replace(r'\n',
                                                    '\n' + ' ' * (linebrk + 8),
                                                    brkcnt - 2)
                        err_line = err_line.replace(r'\n', '')
                    error += err_line
                logging.error(error)
                if 'unauthorized' in error:
                    logging.warning("No valid authentication credentials " +
                                    "found for %s. Please enter credentials " +
                                    "below. In order to avoid this in the " +
                                    "future, please log in to your Docker " +
                                    "Client.", repo)
                    kwargs = docker_login(kwargs)
                    push_image(client, repo, kwargs)
            else:
                logging.info(result)

def docker_login(kwargs):
    kwargs['auth_config'] = {'username': input("Username: "),
                             'email': input("Email: "),
                             'password': getpass()}
    return kwargs

def main(args=None):
    parser = ArgumentParser(description="Publish docker image")
    if __name__ != '__main__':
        parser.prog += " docker " + __name__.rsplit('.', 1)[-1]
        
    repo = os.path.basename(os.getcwd())
    
    client = docker.from_env()
    
    try:
        registry, namespace = find_registry_namespace(client, repo)
    except:
        logging.exception("%s requires a running docker daemon. Please " +
                          "start or install one from %s before trying again.",
                          parser.prog,
                          "https://www.docker.com/community-edition#/download")
        sys.exit(1)
    
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
    tag = get_version('.')
    parser.add_argument('-t', '--tag', help="Version of the image or task " + \
                        "(default: {})".format(tag or 'latest'), default=tag)
    
    args = parser.parse_args(args)
    
    repo = args.namespace + '/' + args.repository
    if args.registry is not None:
        repo = args.registry + '/' + repo
    
    push_kwargs = {'stream': True}
    if args.tag is not None:
        push_kwargs['tag'] = args.tag
    
    push_image(client, repo, push_kwargs)        

if __name__ == '__main__':
    main()
