=============
python-useful
=============

A collection of utilities of everyday use when writing
Python 3.10+ code *or* Django 4.2+ projects.

**Python 2.x support has been dropped.**

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

Using pip::

    pip install useful

If you are about to use the Django features like the templatetags,
you can add to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'useful.django',
    )

Please file an Issue on GitHub if you have bugreport, tip, anything.

Thank you!
