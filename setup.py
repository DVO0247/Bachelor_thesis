from setuptools import setup, find_packages
from pathlib import Path

ROOT_DIR = Path(__file__).parent


def load_requirements():
    with open(ROOT_DIR/'requirements.txt') as file:
        return file.read().splitlines()

setup(
    name='BP',
    author = 'Martin Dvořák',
    version='1.0',
    packages=find_packages(),
    install_requires=load_requirements(),
    entry_points={
        'console_scripts': [
            'manage=django_web.manage:main',
            'receiver=receiver_server.main:main',
            'receiverd=receiver_server.daemon_main:main',
        ],
    },
)
