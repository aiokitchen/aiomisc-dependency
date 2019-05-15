import os

from setuptools import setup, find_packages


from importlib.machinery import SourceFileLoader


module_name = 'aiomisc_dependency'

try:
    version = SourceFileLoader(
        module_name,
        os.path.join(module_name, 'version.py')
    ).load_module()

    version_info = version.version_info
except FileNotFoundError:
    version_info = (0, 0, 0)


__version__ = '{}.{}.{}'.format(*version_info)


def load_requirements(fname):
    """ load requirements from a pip requirements file """
    with open(fname) as f:
        line_iter = (line.strip() for line in f.readlines())
        return [line for line in line_iter if line and line[0] != '#']


setup(
    name=module_name,
    version=__version__,
    author='Yuri Shikanov',
    author_email='dizballanze@gmail.com',
    license='MIT',
    description='aiomisc-dependency - dependency injection in aiomisc',
    long_description=open("README.rst").read(),
    platforms="all",
    classifiers=[
        "Framework :: Pytest",
        'Intended Audience :: Developers',
        'Natural Language :: Russian',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    packages=find_packages(exclude=['tests']),
    install_requires=load_requirements('requirements.txt'),
    extras_require={
        'develop': load_requirements('requirements.dev.txt'),
        ':python_version < "3.7"': 'async-generator',
    },
    entry_points={
        "aiomisc.plugins": ["dependency = aiomisc_dependency.plugin"]
    },
    url='https://github.com/aiokitchen/aiomisc-dependency',
)
