# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import click

from .config import Settings
from . import aws_commands
from . import cleanup as cleanup_commands
from . import test_env as test_env_commands


@click.group()
@click.option('--config', default='calypso.yml')
@click.pass_context
def main(ctx, config=None):
    if not config:
        ctx.obj = {}
    else:
        ctx.obj = {'settings': Settings(config)}


@main.group()
def test_env():
    pass


test_env.add_command(test_env_commands.create)
test_env.add_command(test_env_commands.create_database)
test_env.add_command(test_env_commands.build)
test_env.add_command(test_env_commands.deploy)
test_env.add_command(test_env_commands.destroy)


@main.group()
def aws():
    pass


aws.add_command(aws_commands.instances)
aws.add_command(aws_commands.run)


@main.group()
def cleanup():
    pass


cleanup.add_command(cleanup_commands.app_versions)
