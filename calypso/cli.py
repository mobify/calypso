# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import click

from . import aws_commands
from . import test_env as test_env_commands


@click.group()
def main():
    pass


@main.group()
def test_env():
    pass


test_env.add_command(test_env_commands.create)
test_env.add_command(test_env_commands.build)
test_env.add_command(test_env_commands.deploy)
test_env.add_command(test_env_commands.destroy)


@main.group()
def aws():
    pass


aws.add_command(aws_commands.instances)
