from setuptools import setup, find_packages
from setuptools.command.install import install
from pathlib import Path
import subprocess

ROOT_DIR = Path(__file__).parent

class PostInstall(install):
    def run(self):
        # Spustí standardní instalaci
        install.run(self)

        # Spustí Django management příkazy
        django_web_path = ROOT_DIR/'django_web'
        commands = (
            ['python', 'manage.py', 'makemigrations', 'control_center'],
            ['python', 'manage.py', 'migrate'],
            ['python', 'manage.py', 'collectstatic', '--clear', '--noinput'],
        )

        for command in commands:
            try:
                subprocess.check_call(command, cwd=django_web_path)
            except subprocess.CalledProcessError as e:
                print(f'Error while executing command {command}: {e}')


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
            'receiver=receiver_server'
        ],
    },
    cmdclass={
        "install": PostInstall,
    },
)