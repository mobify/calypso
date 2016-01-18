calypso
#######


.. image:: https://travis-ci.org/mobify/calypso.svg?branch=master
   :target: https://travis-ci.org/mobify/calypso


`calypso` is a small commandline client that streamlines the use of
Docker with Amazon Beanstalk and the test, build and deployment workflow that
we are using at Mobify for some of our services.


Install & Setup
===============

`calypso` is currently still in very early development. The easiest way to 
install it is straight from github::

    $ pip install https://github.com/mobify/calypso/archive/master.zip

Calypso requires a configuration file called `calypso.yml` in the directory you
are running the CLI from. This is most likely your projects root directory.
More details on the structure of the config file will be added here soon.

In addition to a `calypso.yml` file, you'll also need credentials for AWS to 
use most commands. You should export the following environment variables::

    $ export AWS_ACCESS_KEY_ID=<your API key>
    $ export AWS_SECRET_ACCESS_KEY=<your API secret>


AWS related commands
====================

Get the public IP for the EC2 instance (or instances) for a specific Beanstalk
environment::

    $ calypso aws instances my-beanstalk-env
    Instances for my-beanstalk-env
    ------------------------------

    Public DNS: ec2-11-11-11-111.compute-1.amazonaws.com
    Public DNS: ec2-11-11-11-111.compute-1.amazonaws.com

Get a shell within the Docker container running on your Beanstalk EC2 instance
using `docker exec`::

    $ calypso aws run <YOUR APP NAME> <COMMAND>


Cleanup Beanstalk Appplication Versions
=======================================

The number of Beanstalk application versions can grow quite quickly if you
deploy often...and there is a maximum number of versions that you are allowed
to have. This script cleans up all versions except for the last `X`::

    $ calypso cleanup app_versions --keep 10

You can also test which versions would be removed without actually deleting
them::

    $ calypso cleanup app_versions --keep 10 --dry-run


Creating Test Environments
==========================


Create new environment
----------------------

.. code:: bash
    $ calypso test_env create <test_env_name>


Build Docker image
------------------

.. code:: bash
    $ calypso test_env build 


Deploy image to environment
---------------------------

.. code:: bash
    $ calypso test_env deploy <test_env_name>


Development
===========


Install the `calypso` package in development mode with the `test` requirements:

.. code:: bash

    $ pip install -e ".[test]"


License
=======

This code is licensed under the `MIT License`_.

.. _`MIT License`: https://github.com/mobify/calypso/blob/master/LICENSE
