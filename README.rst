calypso
#######


.. image:: https://travis-ci.org/mobify/calypso.svg?branch=master
   :target: https://travis-ci.org/mobify/calypso


`calypso` is a small commandline client that streamlines the use of
Docker with Amazon Beanstalk and the test, build and deployment workflow that
we are using at Mobify for some of our services.


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


License
=======

This code is licensed under the `MIT License`_.

.. _`MIT License`: https://github.com/mobify/calypso/blob/master/LICENSE
