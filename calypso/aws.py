# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import os
import boto3


AWS_REGION = 'us-east-1'


def get_client(service):
    return boto3.client(service,
                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                        region_name=AWS_REGION)
