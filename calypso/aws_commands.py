# -*- coding: utf-8 -*-
from __future__ import absolute_import
import click

from .aws import get_client


def get_status_code(response):
    return response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500)


def instance_for_environment(ec2, name):
    response = ec2.describe_instances(
        Filters=[{'Name': 'tag:Name', 'Values': [name]}])

    if get_status_code(response) != 200:
        raise click.ClickException("error retrieving data")

    reservations = response.get('Reservations', [])

    if not reservations:
        raise click.ClickException(
            "couldn't find any instances for {}".format(name))

    instances = []

    for reservation in reservations:
        for instance in reservation.get('Instances', []):

            public_dns = instance.get('PublicDnsName')
            if public_dns:
                instances.append(public_dns)

    return instances


@click.command()
@click.argument('environment')
def instances(environment):
    ec2 = get_client('ec2')

    header = "Instances for {}".format(environment)
    click.echo(header)
    click.echo("-" * len(header))
    click.echo()

    for instance in instance_for_environment(ec2, environment):
        click.echo("Public DNS: {}".format(instance))

    click.echo()
