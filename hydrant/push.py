#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import logging
import json
from six.moves import input
from six import u
from getpass import getpass
from hydrant.util import ArgParser, add_default_arg, initialize_logging
from hydrant.docker_utils import connect_to_daemon
from hydrant.ConfigLoader import ConfigLoader

Description = "Push local Docker image to remote repository"

def find_registry_namespace(client, repo, config, error_on_fail=False):
    '''If a unique registry and/or namespace exists for the given repo in
    the locally tagged images, override any config settings'''
    # TODO: tag the image with user-set registry and/or namespace via either
    #       hydrant.cfg or CLI args before push
    repo_images = [tag for image in client.images.list() \
                   for tag in image.tags if '/' + repo + ':' in tag]
    namespaces = set(image.split('/')[-2] for image in repo_images)
    registries = set(image.split('/')[0] for image in repo_images
                     if image.count('/') == 2)
    registry = config.Registry
    namespace = config.Namespace
    if len(registries) == 1:
        registry = registries.pop()
    if len(namespaces) == 1:
        namespace = namespaces.pop()
    return registry, namespace

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
                logging.info(u(result))

def docker_login(kwargs):
    kwargs['auth_config'] = {'username': input("Username: "),
                             'email': input("Email: "),
                             'password': getpass()}
    return kwargs

def main(args=None):
    # TODO: allow bulk pushes from the workspace level like with build
    docker_cfg = ConfigLoader().config.Docker
    parser = ArgParser(description=Description)

    # Because parser.prog is initialized to the name of the top-level calling
    # module, it needs to be modified here to be consistent.
    # (i.e. so hydrant docker push -h returns a usage that begins with
    # hydrant docker push rather than only hydrant)
    if __name__ != '__main__':
        parser.prog += " docker " + __name__.rsplit('.', 1)[-1]
        
    repo = os.path.basename(os.getcwd())
    
    client = connect_to_daemon()
    
    try:
        registry, namespace = find_registry_namespace(client, repo, docker_cfg)
    except Exception as e:
        logging.exception(str(e))
        sys.exit(1)
        
    registry = registry or docker_cfg.Registry
    namespace = namespace or docker_cfg.Namespace
    
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
    tag = docker_cfg.Tag
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
    initialize_logging()
    main()
