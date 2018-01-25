import os
from setuptools import setup, find_packages
from hydrant.__about__ import __version__
_README           = os.path.join(os.path.dirname(__file__), 'README.md')
_LONG_DESCRIPTION = open(_README).read()

# Setup information
setup(
    name = 'hydrant',
    version = __version__,
    packages = find_packages(),
    description = 'Hydrant: A tool for installing workflows into FireCloud',
    author = 'Broad Institute CGA Genome Data Analysis Center',
    author_email = 'gdac@broadinstitute.org',
    long_description = _LONG_DESCRIPTION,
    url = 'https://github.com/broadinstitute/HydrantFC',\
    entry_points = {
        'console_scripts': [
            'hydrant = hydrant.hydrant:main'
        ]
    },
    package_data = {'hydrant': ['util/options.json', 'util/runcromw.sh']},
    test_suite = 'nose.collector',
    tests_require = ['nose'],
    install_requires = [
        'firecloud',
        'docker',
        'six'
    ],
    classifiers = [
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    ]
)
