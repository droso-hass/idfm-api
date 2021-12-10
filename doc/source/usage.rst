.. _usage:

Usage
=====

.. _installation:

Installation
------------

To use IDFM-API, first install it using pip:

.. code-block:: console

    pip install idfm_api

Usage
-----

You can use the ``cli.py`` file at the root of this repo to test this package in an interactive way.
The documentations for the available functions is available here.

Building
--------

To build this package, you need to install the dependancies:

.. code-block:: console

    pip install requests beautifulsoup4 build twine

Run the ``export.py`` file to retreive and export the lines from Ile de France mobilité's website to the `idfmèapi/list.json` file
Then run ``python -m build`` to generate the packages.
