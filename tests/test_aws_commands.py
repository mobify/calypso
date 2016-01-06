# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from .botomax import Botomax

from calypso.aws import get_client
from calypso import aws_commands


def test_instance_for_environment():
    ec2 = get_client('ec2')

    with Botomax(ec2) as vcr:
        vcr.use_cassette('instance_for_environment')
        aws_commands.instance_for_environment(ec2, 'portalStaging-env')
