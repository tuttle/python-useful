from os.path import dirname, join
from setuptools import setup

import useful

with open(join(dirname(__file__), 'README.md')) as readme_file:
    long_description = readme_file.read()

setup(
	name='useful',
	version=useful.__versionstr__,
	packages=('useful',),
	package_data={'useful': ['django/locale/cs/LC_MESSAGES/django.*']},
	description="Everyday use utilities for writing Python/Django apps",
	long_description=long_description,
	author="Vlada Macek",
	author_email="macek@sandbox.cz",
	url="https://github.com/tuttle/python-useful",
	license='BSD License',

    zip_safe=False,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: WWW",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Topic :: Software Development :: Libraries",
    ],
)
