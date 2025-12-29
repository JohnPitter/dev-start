"""Setup script for dev-start."""
from setuptools import setup, find_packages

setup(
    name='dev-start',
    version='1.0.0',
    description='Technology configurator for developers',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'requests>=2.31.0',
        'gitpython>=3.1.40',
        'click>=8.1.7',
        'colorama>=0.4.6',
        'PyYAML>=6.0.1',
    ],
    entry_points={
        'console_scripts': [
            'dev-start=src.cli:main',
        ],
    },
    python_requires='>=3.8',
)
