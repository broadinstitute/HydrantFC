import os
from setuptools import setup, find_packages
_README           = os.path.join(os.path.dirname(__file__), 'README.rst')
_LONG_DESCRIPTION = open(_README).read()

# Setup information
setup(
    name = 'hydrant',
    packages = find_packages(),
    description = 'Hydrant: A tool for installing workflows into FireCloud',
    author = 'Broad Institute CGA Genome Data Analysis Center',
    author_email = 'gdac@broadinstitute.org',
    long_description = _LONG_DESCRIPTION,
    license = "BSD 3-Clause License",
    url = 'https://github.com/broadinstitute/HydrantFC',
    entry_points = {
        'console_scripts': [
            'hydrant = hydrant.hydrant:main'
        ]
    },
    package_data = {'hydrant': ['util/*', 'defaults/*.cfg']},
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    test_suite = 'nose.collector',
    tests_require = ['nose'],
    install_requires = [
        'firecloud',
        'docker[tls]>=3.0.1',
        'six'
    ],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
    ]
)
