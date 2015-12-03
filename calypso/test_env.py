#!/usr/env/bin python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import time
import click
import subprocess


from .aws import get_client


def get_env_var(key, value):
    return {'OptionName': key,
            'Namespace': 'aws:elasticbeanstalk:application:environment',
            'Value': value}


def allow_rds_access(environment):
    ec2 = get_client('ec2')
    rds = get_client('rds')

    stack_name = 'awseb-{}-stack'.format(environment['EnvironmentId'])
    click.echo('Adding access to RDS for {}'.format(stack_name))

    groups = []
    while not groups:
        groups = ec2.describe_security_groups(
            Filters=[{'Name': 'tag-value', 'Values': [stack_name]}]
        ).get('SecurityGroups', [])
        click.echo('.', nl=False)
        time.sleep(5)

    group = groups[0]

    response = rds.authorize_db_security_group_ingress(
        DBSecurityGroupName=DB_SECURITY_GROUP,
        EC2SecurityGroupName=group['GroupName'],
        EC2SecurityGroupOwnerId=EC2_GROUP_OWNER_ID)
    print(response)


def clone_environment(app_name, template_env_name, new_env_name, env_config,
                      branch_name):
    beanstalk = get_client('elasticbeanstalk')

    template_env = beanstalk.describe_environments(
        ApplicationName=app_name,
        EnvironmentNames=[template_env_name]).get('Environments', [])[0]

    template_settings = beanstalk.describe_configuration_settings(
        ApplicationName=app_name,
        EnvironmentName=template_env_name).get('ConfigurationSettings', [])[0]

    click.echo(
        'Retrieved settings and env details for {}'.format(template_env_name))

    option_settings = []
    for option in template_settings.get('OptionSettings', []):
        if option.get('OptionName') in 'DATABASE_URL':
            template_database_url = option.get('Value', '')
        if option.get('OptionName') in 'CACHE_URL':
            template_cache_url = option.get('Value', '')

        if option.get('OptionName') in WHITELISTED_SETTINGS and option.get('Value'):
            option_settings.append(option)
            continue

        if option.get('Namespace') == 'aws:elasticbeanstalk:application:environment':
            option_settings.append(option)

    base_url, __ = template_database_url.rsplit('/', 1)
    database_url = '{base_url}/{name}'.format(base_url=base_url,
                                              name=branch_name.replace('-', '_'))

    cache_url = '{base_url}?key_prefix%3D{name}'.format(base_url=template_cache_url,
                                                        name=branch_name)

    option_settings += [
        get_env_var('HOSTNAME', branch_name),
        get_env_var('BRANCH', branch_name),
        get_env_var('BROKER_HASH', branch_name),
        get_env_var('DATABASE_URL', database_url),
        get_env_var('CACHE_URL', cache_url),
        get_env_var('CELERY_QUEUES', branch_name),
    ] + TEST_ENV_OPTIONS

    env_option_settings = list(option_settings)

    for key, value in env_config.get('environment', {}).iteritems():
        env_option_settings.append(get_env_var(key, value))

    return beanstalk.create_environment(
        ApplicationName=app_name,
        EnvironmentName=new_env_name,
        Description="Test environment for branch '{}'".format(branch_name),
        VersionLabel=template_env.get('VersionLabel'),
        SolutionStackName=template_env.get('SolutionStackName'),
        OptionSettings=env_option_settings)


def get_environment_name(branch_name, _type):
    # FIXME: needs proper regex: contain only letters, digits, and the dash character
    branch_name = branch_name[:19].replace('/', '-').replace('_', '-')
    return '{}-{}'.format(branch_name[:19], _type)


@click.command()
@click.option('--branch', default=None)
@click.argument('environment_name')
@click.pass_context
def create(ctx, branch, environment_name):
    beanstalk = get_client('elasticbeanstalk')
    settings = ctx.obj['settings']

    template_settings = settings.get('environment-template')
    if not template_settings:
        raise click.ClickException(
            "creating a test environment requires a 'environment-template' "
            "in the settings file")

    application_name = template_settings.get('application')

    if not template_settings:
        raise click.ClickException(
            'no application name set for environment template')

    # FIXME: We need to setup a loadbalancer otherwise, the whole thing won't
    # work

    # TODO: generate a new password for the DB and update the DATABASE_URL

    if len(environment_name) > 19:
        raise click.ClickException(
            'Environment cannot be more than 19 characters. Aborting.')

    branch_name = branch or os.getenv('CIRCLE_BRANCH', '')
    if not branch_name:
        branch_name = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'])

    branch_name = branch_name.replace('_', '-').replace('/', '-')

    click.echo('Creating env for branch: {}'.format(branch_name))

    beanstalk_envs = beanstalk.describe_environments(
        ApplicationName=application_name).get('Environments', [])

    existing_envs = [e.get('EnvironmentName') for e in beanstalk_envs]

    environments = template_settings.get('environments', {})

    for env_type, env_config in environments.iteritems():
        template_env_name = env_config.get('template')
        env_name = get_environment_name(environment_name, env_type)

        if env_name in existing_envs:
            print env_name, 'already exists, skipping it'
            continue

        #TODO: also check if the BRANCH var is set

        print 'Creating', env_name, 'from', template_env_name

        new_env = clone_environment(app_name=APPLICATION_NAME,
                                    template_env_name=template_env_name,
                                    new_env_name=env_name,
                                    env_config=env_config,
                                    branch_name=branch_name)

        allow_rds_access(new_env)


@click.command()
@click.argument('environment_name')
@click.pass_context
def create_database(context, environment_name):
    beanstalk = get_client('elasticbeanstalk')
    rds = get_client('rds')

    settings = context.obj['settings']

    template_settings = settings.get('environment-template')
    if not template_settings:
        raise click.ClickException(
            "creating a test environment requires a 'environment-template' "
            "in the settings file")

    application_name = template_settings.get('application')

    env_type = template_settings.get('environments', {}).keys()[0]
    env_name = get_environment_name(environment_name, env_type)

    response = beanstalk.describe_configuration_settings(
        ApplicationName=application_name,
        EnvironmentName=env_name).get('ConfigurationSettings', [])[0]

    template_database_url = None

    for option in response.get('OptionSettings', []):
        if option.get('OptionName') in 'DATABASE_URL':
            template_database_url = option.get('Value', '')
            break

    url, database = template_database_url.rsplit('/', 1)
    db_engine = create_engine(url)

    conn = db_engine.connect()

    db_name = database.replace('-', '_')
    conn.execute("CREATE DATABASE IF NOT EXISTS {}".format(db_name))
    conn.close()


@click.command()
@click.option('--version', default=None)
@click.option('--image', default='quay.io/mobify/portal-app')
@click.option('--nobuild', default=False, is_flag=True)
@click.argument('environment_name')
@click.pass_context
def build(context, version, image, nobuild, environment_name):
    settings = context.obj['settings']['environment-template']

    if not nobuild:
        click.echo('Creating new image')

        for command in settings.get('build', []):
            subprocess.call(command.split(' '))

    if not version:
        git_sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
        version = '{}-{}'.format(git_sha, environment_name)

    tagged_image = '{}:{}'.format(image, version)

    click.echo('Tagging and pushing the image: {}'.format(tagged_image))

    subprocess.call(['docker', 'tag', image, tagged_image])

    subprocess.call(['docker', 'push', tagged_image])


#FIXME: add a 'rebuild' flag that removes an existing image and application version
@click.command()
@click.option('--version', default=None)
@click.argument('environment_name')
@click.pass_context
def deploy(context, version, environment_name):
    DOCKERRUN_FILE = 'Dockerrun.aws.json'

    settings = context.obj['settings']['environment-template']

    application_name = settings['application']
    bucket_name = settings['deploy'].get('bucket', '')
    env_types = settings['environments'].keys()

    if not bucket_name:
        raise click.ClickException(
            'no bucket name specified for Beanstalk deployment')

    git_command = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
    branch_name = subprocess.check_output(git_command).strip()

    if not version:
        version_command = ['git', 'rev-parse', '--short', 'HEAD']
        git_sha = subprocess.check_output(version_command).strip()
        version = '{}-{}'.format(git_sha, environment_name)

    if len(environment_name) > 19:
        environment_name = environment_name[:19].replace('_', '-').replace('/', '-')

    beanstalk = get_client('elasticbeanstalk')
    beanstalk_envs = beanstalk.describe_environments(
        ApplicationName=application_name).get('Environments', [])

    existing_envs = [e.get('EnvironmentName') for e in beanstalk_envs]
    if '{}-web'.format(environment_name) not in existing_envs:
        click.echo('no evironment created, skipping deployment')
        return

    click.echo("Deploying {} as {}".format(branch_name, version))

    BEANSTALK_DEPLOY_ZIP = '{app_name}_{version}.zip'.format(
        app_name=application_name,
        version=version)

    # create dockerrun file
    with open('Dockerrun.aws.json.template') as dockerrun_template:
        dockerrun = dockerrun_template.read().replace('<TAG>', version)

    with open('Dockerrun.aws.json', 'w') as dockerrun_file:
        dockerrun_file.write(dockerrun)

    # # We need to generate a ZIP archive for EB so we can use the
    # # .ebextension scripts for customizing our EC2 instances
    subprocess.check_output(
        ['zip', '-r', BEANSTALK_DEPLOY_ZIP, '.ebextensions', DOCKERRUN_FILE])

    click.echo('Uploading beanstalk ZIP to S3.')

    s3 = get_client('s3')
    s3.upload_file(BEANSTALK_DEPLOY_ZIP, bucket_name, BEANSTALK_DEPLOY_ZIP)

    description = "Test version for {} created from branch '{}'".format(
        environment_name,
        branch_name)

    click.echo('Create new version label: {}'.format(version))
    beanstalk.create_application_version(
        ApplicationName=application_name,
        VersionLabel=version,
        SourceBundle={'S3Bucket': bucket_name,
                      'S3Key': BEANSTALK_DEPLOY_ZIP},
        Description=description,
    )

    for env_type in env_types:
        env_name = get_environment_name(environment_name, env_type)

        click.echo("Updating environment {}".format(env_name))

        beanstalk.update_environment(EnvironmentName=env_name,
                                     VersionLabel=version)

    os.remove(DOCKERRUN_FILE)
    os.remove(BEANSTALK_DEPLOY_ZIP)


@click.command()
@click.argument('environment_name')
@click.option('--keep-resources', is_flag=True, default=False)
@click.pass_context
def destroy(context, environment_name, keep_resources):
    beanstalk = get_client('elasticbeanstalk')

    settings = context.obj['settings']['environment-template']
    env_types = settings['environments'].keys()

    click.confirm(
        "Are you sure you want to terminate all '{}' environments?".format(
            environment_name), abort=True)

    for env_type in env_types:
        env_name = get_environment_name(environment_name, env_type)

        beanstalk.terminate_environment(EnvironmentName=env_name,
                                        TerminateResources=(not keep_resources))
