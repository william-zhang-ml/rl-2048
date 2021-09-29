""" Installation configuration. """
from setuptools import setup


setup(
    name='rl-2048',
    version='0.0.1',
    url="https://github.com/william-zhang-ml/rl-2048",
    author="William Zhang",
    author_email="william.zhang.ml@gmail.com",
    packages=['rl_2048'],
    install_requires=[
        'torch>=1.8.1',
        'numpy>=1.18.5'
    ]
)
