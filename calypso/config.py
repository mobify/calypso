# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import os
import yaml


class ConfigError(Exception):
    pass


class Settings(dict):
    """
    The structure of the settings defined in a yaml file::

        amazon:
            security_group: portalstaging
            group_owner_id: '787649934531'
    """

    def __init__(self, filename):

        if not os.path.exists(filename):
            raise ConfigError('config file {} does not exist'.format(filename))

        with open(filename) as config_file:
            config_data = yaml.safe_load(config_file.read())

        self._raw = config_data
        self.update(config_data)
