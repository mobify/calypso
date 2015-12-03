# -*- coding: utf-8 -*-
from __future__ import absolute_import
import click

from collections import namedtuple
from botocore.exceptions import ClientError

from .aws import get_client

ApplicationVersion = namedtuple('ApplicationVersion', ['label', 'date_created'])


@click.command()
@click.argument('app_name')
@click.option('--keep', default=20)
@click.option('--dry-run', default=False, is_flag=True)
def app_versions(app_name, keep, dry_run):
    beanstalk = get_client('elasticbeanstalk')

    response = beanstalk.describe_application_versions(
        ApplicationName=app_name)

    versions = response.get('ApplicationVersions', [])
    if not versions:
        click.secho('No versions found for Beanstalk '
                    'App: {}'.format(app_name),
                    fg='red')
        return

    app_versions = []
    for version_dict in versions:
        version = ApplicationVersion(version_dict.get('VersionLabel'),
                                     version_dict.get('DateCreated'))
        app_versions.append(version)

    app_versions = sorted(app_versions,
                          key=lambda n: n.date_created,
                          reverse=True)

    delete_versions = app_versions[keep:]

    if dry_run:
        click.secho('Dry Run: no changes will be made', fg='yellow')

    for version in delete_versions:
        click.echo('Delete {} created: {}'.format(version.label,
                                                  version.date_created))

        if not dry_run:
            try:
                response = beanstalk.delete_application_version(
                    ApplicationName=app_name,
                    VersionLabel=version.label,
                    DeleteSourceBundle=True)
            except ClientError as exc:
                msg = unicode(exc)
                if 'source bundle: Not Found' in msg:
                    pass
                else:
                    click.ClickException(
                        'Could not delete version {}: {}'.format(version.label,
                                                                 msg))

            status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500)  # noqa

            if status_code != 200:
                click.secho('Deleting version {} failed.'.format(version.label),
                            fg='red')
            else:
                click.secho('Deleted version {}.'.format(version.label), fg='green')
