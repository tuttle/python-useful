=============
python-useful
=============

A collection of utilities of everyday use when writing
Python 2.7 code *or* Django projects.

Overview
--------

This package is used by several living projects. The individual utilities
contained are usually not depending on each other. Their layout and API
are considered stable honouring the backward compatibility.

The project is divided into two sections:

* **General Python stuff**
* **Django-related utils** - located in the ``django`` package

The code is documented, please find the description and examples
in the docstring of each utility.

Installation
------------

Install either using pip::

    pip install useful

Or using e-i::

    easy_install useful

Or from source::

    git clone https://github.com/tuttle/python-useful src/useful
    cd src/useful
    python setup.py develop

If you are about to use the Django features like the templatetags,
you can add to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'useful.django',
    )

Please file an Issue on GitHub if you have bugreport, tip, anything.
Thank you!
