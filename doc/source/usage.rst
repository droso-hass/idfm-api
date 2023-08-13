.. _usage:

Usage
=====

.. _installation:

Installation
------------

This package is available on `PyPI <https://pypi.org/project/idfm-api/>`_ .
This package is based on the official API from `PRIM <https://prim.iledefrance-mobilites.fr/fr>`_ .
To use IDFM-API, first install it using pip:

.. code-block:: console

    pip install idfm_api

Usage
-----

First, you need to create an account on the PRIM website and get your API key `here <https://prim.iledefrance-mobilites.fr/fr/mon-jeton-api>`_ .

You can then use the ``cli.py`` file at the root of this repo to test this package in an interactive way.
The transport line selection might thake a while as we fetch and process the datasets at runtime.
The documentations for the available functions is available here: :doc:`idfm_api`

Building
--------

To build this package, you need to install the dependancies:

.. code-block:: console

    pip install requests build twine

Run ``python -m build`` to generate the packages.
